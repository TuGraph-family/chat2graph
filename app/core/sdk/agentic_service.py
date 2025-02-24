import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import yaml  # type: ignore

from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.singleton import Singleton
from app.core.common.type import PlatformType
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA
from app.core.sdk.wrapper.agent_wrapper import AgentWrapper
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.sdk.wrapper.session_wrapper import SessionWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.session_service import SessionService
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool


class AgenticService(metaclass=Singleton):
    """Agentic service class"""

    def __init__(self, service_name: Optional[str] = None):
        self._service_name = service_name or "Chat2Graph"

        # initialize the services
        self._session_service = SessionService()
        self._agent_service = AgentService()
        self._job_service = JobService()
        self._toolkit_service = ToolkitService()

    def session(self, session_id: Optional[str] = None) -> SessionWrapper:
        """Get the session, if not exists or session_id is None, create a new one."""
        return SessionWrapper().session(session_id=session_id)

    async def execute(self, message: ChatMessage) -> ChatMessage:
        """Execute the service synchronously."""
        job_wrapper = JobWrapper(
            Job(goal=message.get_payload(), assigned_expert_name=message.get_assigned_expert_name())
        )

        # execute the job
        await job_wrapper.execute()

        # get the result of the job
        job_result: JobResult = await job_wrapper.result()
        return job_result.result

    def train_toolkit(self, id: str, *args, **kwargs) -> Any:
        """Train the toolkit."""
        self._toolkit_service.train(id=id, *args, **kwargs)

    def train_workflow(self, workflow_wrapper: WorkflowWrapper, *args, **kwargs) -> Any:
        """Train the workflow."""
        # TODO: implement the train workflow
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
        """Load the configuration of the agentic service."""

        def _load_action(action_config: Dict[str, Any]) -> Action:
            """Load a single action."""
            tools: List[Tool] = []

            # configure the tools
            for tool_config in action_config.get("tools", []):
                module = importlib.import_module(tool_config["module_path"])
                tool_class = getattr(module, tool_config["tool"])
                tools.append(tool_class(id=tool_config.get("id", str(uuid4()))))

            # configure the action
            return Action(
                id=action_config.get("id", str(uuid4())),
                name=action_config["name"],
                description=action_config["desc"],
                tools=tools,
            )

        def _load_operator(operator_config: Dict[str, Any]) -> OperatorWrapper:
            """Load a single operator."""
            operator: OperatorWrapper = (
                OperatorWrapper()
                .instruction(operator_config["instruction"])
                .output_schema(operator_config.get("output_schema", ""))
                .actions(
                    [_load_action(act_config) for act_config in operator_config.get("actions", [])]
                )
                .build()
            )

            if toolkit := operator_config.get("toolkit", None):
                # handle with all tuple types of actions
                for chain in toolkit.get("chain", None):
                    operator = operator.toolkit_chain(
                        tuple(_load_action(act_config) for act_config in chain)
                    )

                # handle all single actions
                for act_config in toolkit.get("single", []):
                    operator = operator.toolkit_chain(_load_action(act_config))

            return operator

        # load the yaml file
        with open(yaml_path, encoding=encoding) as f:
            config = yaml.safe_load(f)

        app_config = config.get("app", {})

        # get the plugin configuration
        plugin = config.get("plugin", {})
        platform = plugin.get("platform", None)
        platform_type = PlatformType(platform) if platform else None

        # start the agentic service
        mas = AgenticService(app_config.get("name", "Chat2Graph"))

        # configure the leader
        job_decomposition_operator = (
            OperatorWrapper()
            .instruction("Please decompose the task.")
            .output_schema(JOB_DECOMPOSITION_OUTPUT_SCHEMA)
            .build()
        )
        mas.leader(name="Leader Test").reasoner(
            thinker_name="Leader", actor_name="Leader"
        ).workflow(job_decomposition_operator, platfor_type=platform_type).build()

        # configure the experts
        for expert in config.get("experts", []):
            # configure the profile and the reasoner of the expert
            expert_wrapper = mas.expert(
                name=expert["profile"]["name"], description=expert["profile"].get("desc", "")
            ).reasoner(
                actor_name=expert["reasoner"]["actor_name"],
                thinker_name=expert["reasoner"].get("thinker_name", None),
            )

            # configure the workflow
            if workflow := expert["workflow"]:
                # handle with all tuple types of operators
                for chain in workflow.get("chain", []):
                    expert_wrapper = expert_wrapper.workflow(
                        tuple(_load_operator(operator_config) for operator_config in chain),
                        platfor_type=platform_type,
                    )

                # handle all single operators
                for operator_config in workflow.get("single", []):
                    expert_wrapper = expert_wrapper.workflow(
                        _load_operator(operator_config), platfor_type=platform_type
                    )

            expert_wrapper.build()

        return mas
