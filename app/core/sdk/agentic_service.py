import importlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from mcp.types import Tool as McpBaseTool

from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.async_func import run_async_function
from app.core.common.singleton import Singleton
from app.core.common.type import ReasonerType, WorkflowPlatformType
from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.model.agentic_config import AgenticConfig, LocalToolConfig
from app.core.model.graph_db_config import GraphDbConfig
from app.core.model.job import Job
from app.core.model.message import ChatMessage, MessageType, TextMessage
from app.core.prompt.job_decomposition import (
    JOB_DECOMPOSITION_OUTPUT_SCHEMA,
    JOB_DECOMPOSITION_PROMPT,
)
from app.core.sdk.wrapper.agent_wrapper import AgentWrapper
from app.core.sdk.wrapper.graph_db_wrapper import GraphDbWrapper
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.sdk.wrapper.session_wrapper import SessionWrapper
from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.core.service.reasoner_service import ReasonerService
from app.core.service.service_factory import ServiceFactory
from app.core.service.session_service import SessionService
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.mcp_service import McpService
from app.core.toolkit.mcp_tool import McpTool
from app.core.toolkit.tool import Tool
from app.core.toolkit.tool_config import McpConfig


class AgenticService(metaclass=Singleton):
    """Agentic service class"""

    def __init__(self, service_name: Optional[str] = None):
        self._service_name = service_name or "Chat2Graph"

        # initialize the dao
        DaoFactory.initialize(DbSession())

        # initialize the services
        ServiceFactory.initialize()
        self._message_service: MessageService = MessageService.instance
        self._session_service: SessionService = SessionService.instance
        self._agent_service: AgentService = AgentService.instance
        self._job_service: JobService = JobService.instance
        self._toolkit_service: ToolkitService = ToolkitService.instance
        self._reasoner_service: ReasonerService = ReasonerService.instance

    @property
    def name(self) -> str:
        """Get the name of the agentic service."""
        return self._service_name

    def session(self, session_id: Optional[str] = None) -> SessionWrapper:
        """Get the session, if not exists or session_id is None, create a new one."""
        return SessionWrapper(self._session_service.get_session(session_id=session_id))

    def execute(self, message: Union[TextMessage, str]) -> ChatMessage:
        """Execute the service synchronously."""
        if isinstance(message, str):
            message = TextMessage(message)

        job = Job(
            goal=message.get_payload(),
            assigned_expert_name=message.get_assigned_expert_name(),
        )
        self._job_service.save_job(job=job)
        job_wrapper = JobWrapper(job)

        # execute the job
        job_wrapper.execute()

        # get the result of the job
        result_message: TextMessage = cast(
            TextMessage,
            self._message_service.get_message_by_job_id(
                job_id=job_wrapper.job.id, message_type=MessageType.TEXT_MESSAGE
            ),
        )
        return result_message

    def reasoner(self, reasoner_type: ReasonerType = ReasonerType.DUAL) -> "AgenticService":
        """Chain the reasoner."""
        self._reasoner_service.init_reasoner(reasoner_type)
        return self

    def toolkit(self, *action_chain: Union[Action, Tuple[Action, ...]]) -> "AgenticService":
        """Chain the actions in the toolkit."""
        ToolkitWrapper(self._toolkit_service.get_toolkit()).chain(*action_chain)
        return self

    def tune_toolkit(self, id: str, *args, **kwargs) -> Any:
        """Train the toolkit."""
        self._toolkit_service.tune(id, *args, **kwargs)

    def tune_workflow(self, expert: Expert, *args, **kwargs) -> Any:
        """Train the workflow."""
        # TODO: implement the tune workflow
        raise NotImplementedError("Train workflow is not implemented yet.")

    def leader(self, name: str, description: Optional[str] = None) -> AgentWrapper:
        """Set the name of the leader."""
        agent_wrapper = AgentWrapper()
        agent_wrapper.profile(name=name, description=description).type(Leader)

        return agent_wrapper

    def expert(self, name: str, description: Optional[str] = None) -> AgentWrapper:
        """Set the name of the expert."""
        agent_wrapper = AgentWrapper()
        agent_wrapper.profile(name=name, description=description).type(Expert)

        return agent_wrapper

    def graph_db(self, graph_db_config: GraphDbConfig) -> "AgenticService":
        """Set the graph database configuration."""
        GraphDbWrapper(graph_db_config).graph_db()
        return self

    @staticmethod
    def load(
        yaml_path: Union[str, Path] = "app/core/sdk/chat2graph.yml",
        encoding: str = "utf-8",
    ) -> "AgenticService":
        """Configure the AgenticService from yaml file."""

        # 1. load configuration and initialize the service
        print(f"Loading AgenticService from {yaml_path} with encoding {encoding}")
        agentic_service_config = AgenticConfig.from_yaml(yaml_path, encoding)
        mas = AgenticService(agentic_service_config.app.name)

        # 2. initialize the reasoner
        mas.reasoner(reasoner_type=agentic_service_config.reasoner.type)

        # 3. build all actions and configure the toolkit
        actions_dict: Dict[str, Action] = {}  # cache for all created actions: name -> Action

        # the 'toolkit' section in YAML defines chains of actions.
        # iterate through each defined chain to build and register it.
        for action_config_chain in agentic_service_config.toolkit:
            built_action_chain: List[Action] = []

            # iterate through each action's configuration within the current chain.
            for action_config in action_config_chain:
                # build the list of tools for the current action.
                action_tools: List[Tool] = []
                for tool_config in action_config.tools:
                    if isinstance(tool_config, LocalToolConfig):
                        # handle local tools defined by module path and class name.
                        module = importlib.import_module(tool_config.module_path)
                        tool_class = getattr(module, tool_config.name)
                        tool = tool_class()
                        action_tools.append(tool)
                    elif isinstance(tool_config, McpConfig):
                        # handle MCP tools from a remote service.
                        mcp_service = McpService(mcp_config=tool_config)
                        mcp_available_tools: List[McpBaseTool] = run_async_function(
                            mcp_service.list_tools
                        )
                        for mcp_tool_info in mcp_available_tools:
                            tool_description = (
                                f"{mcp_tool_info.description}\n"
                                if mcp_tool_info.description
                                else ""
                            )
                            tool_description += json.dumps(mcp_tool_info.inputSchema, indent=4)

                            tool = McpTool(
                                name=mcp_tool_info.name,
                                description=tool_description,
                                tool_group=mcp_service,
                            )
                            action_tools.append(tool)
                    else:
                        raise ValueError(f"Unsupported tool config type: {type(tool_config)}")

                # create the Action instance with its configured tools.
                action = Action(
                    id=action_config.id,
                    name=action_config.name,
                    description=action_config.desc,
                    tools=action_tools,
                )
                actions_dict[action.name] = action
                built_action_chain.append(action)

            # chain the built actions into the service's toolkit.
            if len(built_action_chain) == 1:
                mas.toolkit(built_action_chain[0])
            elif len(built_action_chain) > 1:
                mas.toolkit(tuple(built_action_chain))
            else:
                raise ValueError("Toolkit chain definition cannot be empty.")

        # 4. configure the Leader Agent
        workflow_platform_type: Optional[WorkflowPlatformType] = (
            agentic_service_config.plugin.get_workflow_platform_type()
        )

        # gather actions for the leader from the previously built actions.
        print("Init the Leader agent")
        leader_actions = [
            actions_dict[action_config.name]
            for action_config in agentic_service_config.leader.actions
        ]

        # build the leader's primary operator for job decomposition.
        job_decomposition_operator = (
            OperatorWrapper()
            .instruction(JOB_DECOMPOSITION_PROMPT)
            .output_schema(JOB_DECOMPOSITION_OUTPUT_SCHEMA)
            .actions(leader_actions)
            .build()
        )

        # build the leader agent with its workflow.
        mas.leader(name="Leader").workflow(
            job_decomposition_operator, platform_type=workflow_platform_type
        ).build()

        # 5. configure Expert Agents
        print("Init the Expert agents")
        for expert_config in agentic_service_config.experts:
            expert_name = expert_config.profile.name
            print(f"  - Configuring expert: {expert_name}")
            expert_wrapper = mas.expert(name=expert_name, description=expert_config.profile.desc)

            # build the workflow for the expert, which can consist of multiple operator chains.
            for op_config_chain in expert_config.workflow:
                operator_chain: List[OperatorWrapper] = []
                for op_config in op_config_chain:
                    # gather actions for the current operator.
                    operator_actions = [
                        actions_dict[action_name] for action_name in op_config.actions
                    ]

                    # build the operator.
                    operator = (
                        OperatorWrapper()
                        .instruction(op_config.instruction)
                        .output_schema(op_config.output_schema)
                        .actions(operator_actions)
                        .build()
                    )
                    operator_chain.append(operator)

                # add the built operator chain to the expert's workflow.
                if len(operator_chain) == 1:
                    expert_wrapper = expert_wrapper.workflow(
                        operator_chain[0], platform_type=workflow_platform_type
                    )
                elif len(operator_chain) > 1:
                    expert_wrapper = expert_wrapper.workflow(
                        tuple(operator_chain), platform_type=workflow_platform_type
                    )
                else:
                    raise ValueError("Operator chain in a workflow definition cannot be empty.")

            # do not set the evaluator in the workflow
            # expert_wrapper.evaluator().build()
            expert_wrapper.build()

        return mas
