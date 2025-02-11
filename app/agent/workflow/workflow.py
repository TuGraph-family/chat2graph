from abc import ABC, abstractmethod
import threading
from typing import Any, List, Optional

import networkx as nx  # type: ignore

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator
from app.core.common.type import WorkflowStatus
from app.core.memory.message import WorkflowMessage


class Workflow(ABC):
    """Workflow is a sequence of operators that need to be executed

    Attributes:
        _operator_graph (nx.DiGraph): The operator graph of the workflow.
        _evaluator (Optional[Operator]): The operator to evaluate the progress of the workflow.
    """

    def __init__(self):
        self.__lock = threading.Lock()
        self.__workflow = None

        self._operator_graph: nx.DiGraph = nx.DiGraph()
        self._evaluator: Optional[Operator] = None

    async def execute(
        self,
        job: Job,
        reasoner: Reasoner,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        """Execute the workflow.

        Args:
            job (Job): The job assigned to the agent.
            reasoner (Reasoner): The reasoner that reasons the operators.
            workflow_messages (Optional[List[WorkflowMessage]]): The workflow messages
                generated by the previous agents.
            lesson (Optional[str]): The lesson learned from the job execution.

        Returns:
            WorkflowMessage: The output of the workflow.
        """

        def build_workflow():
            with self.__lock:
                if self.__workflow is None:
                    self.__workflow = self._build_workflow(reasoner)
                return self.__workflow

        workflow_message = await self._execute_workflow(
            build_workflow(), job, workflow_messages, lesson
        )
        if not self._evaluator:
            workflow_message.status = WorkflowStatus.SUCCESS
            workflow_message.evaluation = "The workflow is executed successfully."
            workflow_message.lesson = ""
        return workflow_message

    def add_operator(
        self,
        operator: Operator,
        previous_ops: Optional[List[Operator]] = None,
        next_ops: Optional[List[Operator]] = None,
    ):
        """Add an operator to the workflow."""
        with self.__lock:
            self._operator_graph.add_node(operator.get_id(), operator=operator)
            if previous_ops:
                for previous_op in previous_ops:
                    if not self._operator_graph.has_node(previous_op.get_id()):
                        self._operator_graph.add_node(previous_op.get_id(), operator=previous_op)
                    self._operator_graph.add_edge(previous_op.get_id(), operator.get_id())
            if next_ops:
                for next_op in next_ops:
                    if not self._operator_graph.has_node(next_op.get_id()):
                        self._operator_graph.add_node(next_op.get_id(), operator=next_op)
                    self._operator_graph.add_edge(operator.get_id(), next_op.get_id())
            self.__workflow = None

    def remove_operator(self, operator: Operator) -> None:
        """Remove an operator from the workflow."""
        with self.__lock:
            self._operator_graph.remove_node(operator.get_id())
            self.__workflow = None

    def set_evaluator(self, evaluator: Operator):
        """Add an evaluator operator to the workflow."""
        self._evaluator = evaluator

    def get_operator(self, operator_id: str) -> Optional[Operator]:
        """Get an operator from the workflow."""
        try:
            return self._operator_graph.nodes[operator_id]["operator"]
        except KeyError as e:
            raise ValueError(f"Operator {operator_id} does not exist in the workflow.") from e

    def get_operators(self) -> List[Operator]:
        """Get all operators from the workflow."""
        return [data["operator"] for _, data in self._operator_graph.nodes() if "operator" in data]

    def visualize(self) -> None:
        """Visualize the workflow."""
        raise NotImplementedError("This method needs to be implemented.")

    @abstractmethod
    def _build_workflow(self, reasoner: Reasoner) -> Any:
        """Build the workflow."""

    @abstractmethod
    async def _execute_workflow(
        self,
        workflow: Any,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        """Execute the workflow."""
