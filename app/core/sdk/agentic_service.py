import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.singleton import Singleton
from app.core.common.type import ReasonerType, WorkflowPlatformType
from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.model.agentic_config import AgenticConfig, ExpertConfig, LocalToolConfig
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
from app.core.toolkit.tool import Tool
from app.core.toolkit.tool_config import McpConfig
from app.core.toolkit.tool_group import ToolGroup


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

    def toolkit(
        self,
        *item_chain: Union[Action, Tool, ToolGroup, Tuple[Union[Action, Tool, ToolGroup], ...]],
    ) -> "AgenticService":
        """Chain the actions in the toolkit."""
        ToolkitWrapper(self._toolkit_service.get_toolkit()).chain(*item_chain)
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
        mas.toolkit(*AgenticService._build_toolkit(agentic_service_config))

        # 4. configure the Leader Agent
        workflow_platform_type: Optional[WorkflowPlatformType] = (
            agentic_service_config.plugin.get_workflow_platform_type()
        )
        mas.leader("Leader").workflow(
            AgenticService._build_leader_workflow(
                agentic_service_config=agentic_service_config,
            ),
            platform_type=workflow_platform_type,
        ).build()

        # 5. configure Expert Agents
        for expert_config in agentic_service_config.experts:
            mas.expert(
                name=expert_config.profile.name,
                description=expert_config.profile.desc,
            ).workflow(
                *AgenticService._build_expert_workflow(
                    expert_config=expert_config,
                    agentic_service_config=agentic_service_config,
                ),
                platform_type=workflow_platform_type,
            ).build()
            # use mas.expert().workflow().evaluator().build() to add evaluator if needed

        return mas

    @staticmethod
    def _build_toolkit(
        agentic_service_config: AgenticConfig,
    ) -> List[Union[Action, Tool, ToolGroup, Tuple[Union[Action, Tool, ToolGroup], ...]]]:
        """Build the toolkit."""
        # the 'toolkit' section in YAML defines chains of actions
        # iterate through each defined chain to build and register it
        item_chain: List[
            Union[Action, Tool, ToolGroup, Tuple[Union[Action, Tool, ToolGroup], ...]]
        ] = []
        for action_config_chain in agentic_service_config.toolkit:
            # process each action separately to avoid tuple connection issues
            for action_config in action_config_chain:
                # create the Action instance with its configured tools.
                action = Action(
                    id=action_config.id,
                    name=action_config.name,
                    description=action_config.desc,
                )

                # collect tools for this action
                action_tools: List[Union[Tool, ToolGroup]] = []

                # process tools and add them to the action
                for tool_config in action_config.tools:
                    if isinstance(tool_config, LocalToolConfig):
                        # handle local tools defined by module path and class name
                        module = importlib.import_module(tool_config.module_path)
                        tool_class = getattr(module, tool_config.name)
                        tool = tool_class()
                        action_tools.append(tool)
                    elif isinstance(tool_config, McpConfig):
                        # handle MCP tools from a remote service as tool group
                        mcp_service = McpService(mcp_config=tool_config)
                        action_tools.append(mcp_service)  # McpService is a subclass of ToolGroup
                    else:
                        raise ValueError(f"Unsupported tool config type: {type(tool_config)}")

                # create individual chain for this action and its tools
                item_chain.append(action)
                if action_tools:
                    if len(action_tools) == 1:
                        # single tool - create simple chain
                        item_chain.append(action_tools[0])
                    else:
                        # multiple tools - create parallel connection
                        item_chain.append((*action_tools,))

        return item_chain

    @staticmethod
    def _build_leader_workflow(agentic_service_config: AgenticConfig) -> OperatorWrapper:
        """Build the leader agent configuration and return workflow components."""
        print("Init the Leader agent")

        actions_dict: Dict[str, Action] = {}  # cache for all created actions: name -> Action

        # the 'toolkit' section in YAML defines chains of actions.
        # iterate through each defined chain to build and register it.
        for action_config_chain in agentic_service_config.toolkit:
            # process each action separately to avoid tuple connection issues
            for action_config in action_config_chain:
                # create the Action instance with its configured tools.
                action = Action(
                    id=action_config.id,
                    name=action_config.name,
                    description=action_config.desc,
                )
                actions_dict[action.name] = action

        # gather actions for the leader from the previously built actions.
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

        return job_decomposition_operator

    @staticmethod
    def _build_expert_workflow(
        expert_config: ExpertConfig,
        agentic_service_config: AgenticConfig,
    ) -> Tuple[Union[OperatorWrapper, Tuple[OperatorWrapper, ...]], ...]:
        """Build a single expert agent configuration and return workflow components."""
        print(f"  - Configuring expert: {expert_config.profile.name}")

        actions_dict: Dict[str, Action] = {}  # cache for all created actions: name -> Action

        # the 'toolkit' section in YAML defines chains of actions.
        # iterate through each defined chain to build and register it.
        for action_config_chain in agentic_service_config.toolkit:
            # process each action separately to avoid tuple connection issues
            for action_config in action_config_chain:
                # create the Action instance with its configured tools.
                action = Action(
                    id=action_config.id,
                    name=action_config.name,
                    description=action_config.desc,
                )
                actions_dict[action.name] = action

        workflow_items: List[Union[OperatorWrapper, Tuple[OperatorWrapper, ...]]] = []

        # build the workflow for the expert, which can consist of multiple operator chains
        for op_config_chain in expert_config.workflow:
            if len(op_config_chain) == 1:
                # single operator - add directly
                op_config = op_config_chain[0]
                operator_actions = [actions_dict[action_name] for action_name in op_config.actions]
                operator = (
                    OperatorWrapper()
                    .instruction(op_config.instruction)
                    .output_schema(op_config.output_schema)
                    .actions(operator_actions)
                    .build()
                )
                workflow_items.append(operator)
            else:
                # multiple operators - create tuple for parallel execution
                operator_chain: List[OperatorWrapper] = []
                for op_config in op_config_chain:
                    operator_actions = [
                        actions_dict[action_name] for action_name in op_config.actions
                    ]
                    operator = (
                        OperatorWrapper()
                        .instruction(op_config.instruction)
                        .output_schema(op_config.output_schema)
                        .actions(operator_actions)
                        .build()
                    )
                    operator_chain.append(operator)
                workflow_items.append(tuple(operator_chain))

        return tuple(workflow_items)
