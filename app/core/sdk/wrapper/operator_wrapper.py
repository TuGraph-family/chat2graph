from typing import Any, List, Optional, Union

from app.core.env.env import EnvService
from app.core.knowledge.knowlege_service import KnowledgeService
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig


class OperatorWrapper:
    """Facade of the operator."""

    def __init__(self):
        self._operator: Optional[Operator] = None

        self._instruction: Optional[str] = None
        self._output_schema: Optional[str] = None
        self._actions: List[Action] = []
        self._toolkit_service: ToolkitService = ToolkitService.instance or ToolkitService()
        self._knowledge_service: Optional[KnowledgeService] = None
        self._environment_service: Optional[EnvService] = None

    @property
    def operator(self) -> Operator:
        """Get the operator."""
        if not self._operator:
            raise ValueError("Operator is not built yet.")
        return self._operator

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

    def service(self, service: Union[KnowledgeService, EnvService]) -> "OperatorWrapper":
        """Set the service of the operator."""
        if isinstance(service, EnvService):
            self._environment_service = service

        elif isinstance(service, KnowledgeService):
            self._knowledge_service = service

        else:
            raise ValueError(f"Invalid service: {service}.")

        return self

    def env_service(self, env: Any) -> "OperatorWrapper":
        """Set the environment service of the operator."""
        # TODO: implement the environment service
        raise NotImplementedError("Environment service is not implemented yet.")

    def knowledge_service(self, knowledge: Any) -> "OperatorWrapper":
        """Set the knowledge service of the operator."""
        # TODO: implement the knowledge service
        raise NotImplementedError("Knowledge service is not implemented yet.")

    def build(self) -> "OperatorWrapper":
        """Build the operator."""
        if not self._instruction:
            raise ValueError("Instruction is required.")
        if not self._output_schema:
            raise ValueError("Output schema is required.")
        if not self._toolkit_service:
            raise ValueError("Toolkit service is required.")

        config = OperatorConfig(
            instruction=self._instruction,
            output_schema=self._output_schema,
            actions=self._actions,
        )

        self._operator = Operator(
            config=config,
            knowledge_service=self._knowledge_service,
            environment_service=self._environment_service,
        )

        return self

    def get_id(self) -> str:
        """Get the operator id."""
        if not self._operator:
            raise ValueError("Operator is not built yet.")
        return self._operator.get_id()
