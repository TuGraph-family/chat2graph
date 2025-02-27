import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.agentic_config import AgenticConfig
from app.core.common.singleton import Singleton
from app.core.common.type import PlatformType, ReasonerType
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA
from app.core.sdk.wrapper.agent_wrapper import AgentWrapper
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.sdk.wrapper.session_wrapper import SessionWrapper
from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.reasoner_service import ReasonerService
from app.core.service.service_factory import ServiceFactory
from app.core.service.session_service import SessionService
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool


class AgenticService(metaclass=Singleton):
    """Agentic service class"""

    def __init__(self, service_name: Optional[str] = None):
        self._service_name = service_name or "Chat2Graph"

        # initialize the services
        ServiceFactory.initialize()
        self._session_service: SessionService = SessionService.instance
        self._agent_service: AgentService = AgentService.instance
        self._job_service: JobService = JobService.instance
        self._toolkit_service: ToolkitService = ToolkitService.instance
        self._reasoner_service: ReasonerService = ReasonerService.instance

    def session(self, session_id: Optional[str] = None) -> SessionWrapper:
        """Get the session, if not exists or session_id is None, create a new one."""
        return SessionWrapper(self._session_service.get_session(session_id=session_id))

    def execute(self, message: ChatMessage) -> ChatMessage:
        """Execute the service synchronously."""
        job_wrapper = JobWrapper(
            Job(goal=message.get_payload(), assigned_expert_name=message.get_assigned_expert_name())
        )

        # execute the job
        job_wrapper.execute()

        # get the result of the job
        job_result: JobResult = job_wrapper.query_result()
        return job_result.result

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
        self._toolkit_service.tune(id=id, *args, **kwargs)

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

    @staticmethod
    def load(
        yaml_path: Union[str, Path] = "app/core/sdk/chat2graph.yml", encoding: str = "utf-8"
    ) -> "AgenticService":
        """Configure the AgenticService from yaml file."""

        agentic_service_config = AgenticConfig.from_yaml(yaml_path, encoding)

        agentic_service_config.export_yaml(yaml_path="app/core/sdk/chat2graph_export.yml")
        agentic_service_config = AgenticConfig.from_yaml(
            "app/core/sdk/chat2graph_export.yml", encoding
        )

        # create an instance of AgenticService
        mas = AgenticService(agentic_service_config.app.name)

        # tools and actions
        tools_dict: Dict[str, Tool] = {}  # name -> Tool
        actions_dict: Dict[str, Action] = {}  # name -> Action

        # configure toolkit by the toolkit chains
        for action_chain in agentic_service_config.toolkit:
            chain: List[Action] = []
            for action_config in action_chain:
                for tool_config in action_config.tools:
                    module = importlib.import_module(tool_config.module_path)
                    tool_class = getattr(module, tool_config.name)
                    tool = tool_class(id=tool_config.id)
                    tools_dict[tool_config.name] = tool

                action = Action(
                    id=action_config.id,
                    name=action_config.name,
                    description=action_config.desc,
                    tools=[tools_dict[tool_config.name] for tool_config in action_config.tools],
                )
                actions_dict[action_config.name] = action
                chain.append(action)

            if len(chain) == 1:
                mas.toolkit(chain[0])
            elif len(chain) > 1:
                mas.toolkit(tuple(chain))
            else:
                raise ValueError("Toolkit chain cannot be empty.")

        # configure the leader
        job_decomposition_operator = (
            OperatorWrapper()
            .instruction("Please decompose the task.")
            .output_schema(JOB_DECOMPOSITION_OUTPUT_SCHEMA)
            .build()
        )

        platform_type = None
        if agentic_service_config.plugin.platform:
            platform_type = PlatformType(agentic_service_config.plugin.platform)

        mas.leader(name="Leader Test").workflow(
            job_decomposition_operator, platform_type=platform_type
        ).build()

        # configure the experts
        for expert_config in agentic_service_config.experts:
            expert_wrapper = mas.expert(
                name=expert_config.profile.name, description=expert_config.profile.desc
            )

            # configure the workflow
            for op_chain in expert_config.workflow:
                operator_chain: List[OperatorWrapper] = []
                for op_config in op_chain:
                    operator_actions: List[Action] = []
                    # get the configurations of the action instance,
                    # by the name of the action from the OperatorConfig
                    operator_actions.extend(
                        [actions_dict[action_name] for action_name in op_config.actions]
                    )

                    operator = (
                        OperatorWrapper()
                        .instruction(op_config.instruction)
                        .output_schema(op_config.output_schema)
                        .actions(operator_actions)
                        .build()
                    )
                    operator_chain.append(operator)

                if len(operator_chain) > 1:
                    expert_wrapper = expert_wrapper.workflow(
                        tuple(operator_chain), platform_type=platform_type
                    )
                elif len(operator_chain) == 1:
                    expert_wrapper = expert_wrapper.workflow(
                        operator_chain[0], platform_type=platform_type
                    )
                else:
                    raise ValueError("Operator chain in the workflow cannot be empty.")

            expert_wrapper.build()

        return mas
