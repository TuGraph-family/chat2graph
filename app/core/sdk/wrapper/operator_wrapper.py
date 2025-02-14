from typing import List, Optional, Union

from app.core.env.env import EnvService
from app.core.knowledge.knowlege_service import KnowledgeService
from app.core.toolkit.action import Action
from app.core.toolkit.toolkit import Toolkit, ToolkitService
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig


class OperatorWrapper:
    """Facade of the operator."""

    def __init__(self):
        self._instruction: Optional[str] = None
        self._output_schema: Optional[str] = None
        self._actions: List[Action] = []
        self._toolkit_service: Optional[ToolkitService] = None
        self._knowledge_service: Optional[KnowledgeService] = None
        self._environment_service: Optional[EnvService] = None

    def instruction(self, instruction: str) -> "OperatorWrapper":
        """Set the instruction of the operator."""
        self._instruction = instruction
        return self

    def output_schema(self, output_schema: str) -> "OperatorWrapper":
        """Set the output schema of the operator."""
        self._output_schema = output_schema
        return self

    def actions(self, actions: List[Action]) -> "OperatorWrapper":
        """Set the actions of the operator."""
        self._actions.extend(actions)
        return self

    def service(
        self, service: Union[ToolkitService, KnowledgeService, EnvService]
    ) -> "OperatorWrapper":
        """Set the service of the operator."""
        if isinstance(service, ToolkitService):
            self._toolkit_service = service

        elif isinstance(service, EnvService):
            self._environment_service = service

        elif isinstance(service, KnowledgeService):
            self._knowledge_service = service

        else:
            raise ValueError(f"Invalid service: {service}.")

        return self

    def toolkit_service(self, toolkit: Toolkit) -> "OperatorWrapper":
        """Set the toolkit service of the operator."""
        return self.service(ToolkitService(toolkit))

    def env_service(self, env: EnvService) -> "OperatorWrapper":
        """Set the environment service of the operator."""
        return self.service(env)

    def knowledge_service(self, knowledge: KnowledgeService) -> "OperatorWrapper":
        """Set the knowledge service of the operator."""
        return self.service(knowledge)

    def build(self) -> Operator:
        """Build the operator."""
        if not self._instruction:
            raise ValueError("Instruction is required.")
        if not self._output_schema:
            raise ValueError("Output schema is required.")
        if len(self._actions) == 0:
            raise ValueError("Actions are required.")
        if not self._toolkit_service:
            raise ValueError("Toolkit service is required.")

        config = OperatorConfig(
            instruction=self._instruction,
            output_schema=self._output_schema,
            actions=self._actions,
        )

        return Operator(
            config=config,
            toolkit_service=self._toolkit_service,
            knowledge_service=self._knowledge_service,
            environment_service=self._environment_service,
        )
