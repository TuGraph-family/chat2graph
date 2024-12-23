import threading
from abc import ABC, abstractmethod
from typing import List, Optional, Any

import networkx as nx  # type: ignore

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator
from app.memory.message import WorkflowMessage


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

    async def execute(self, job: Job, reasoner: Reasoner) -> WorkflowMessage:
        """Execute the workflow.

        Args:
            job (Job): The job assigned to the agent.
            reasoner (Reasoner): The reasoner that reasons the operators.

        Returns:
            WorkflowMessage: The output of the workflow.
        """

        def build_workflow():
            with self.__lock:
                if self.__workflow is None:
                    self.__workflow = self._build_workflow(reasoner)
                return self.__workflow

        return await self._execute_workflow(build_workflow(), job)

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
                        self._operator_graph.add_node(
                            previous_op.get_id(), operator=previous_op
                        )
                    self._operator_graph.add_edge(previous_op.get_id(),
                                                  operator.get_id())
            if next_ops:
                for next_op in next_ops:
                    if not self._operator_graph.has_node(next_op.get_id()):
                        self._operator_graph.add_node(next_op.get_id(),
                                                      operator=next_op)
                    self._operator_graph.add_edge(operator.get_id(),
                                                  next_op.get_id())
            self.__workflow = None

    def remove_operator(self, operator: Operator) -> None:
        """Remove an operator from the workflow."""
        with self.__lock:
            self._operator_graph.remove_node(operator.get_id())
            self.__workflow = None

    def set_evaluator(self, evaluator: Operator):
        """Add an evaluator operator to the workflow."""
        self._evaluator: Optional[Operator] = evaluator

    def get_operator(self, operator_id: str) -> Optional[Operator]:
        """Get an operator from the workflow."""

    def get_operators(self) -> List[Operator]:
        """Get all operators from the workflow."""

    def visualize(self) -> None:
        """Visualize the workflow."""

    @abstractmethod
    def _build_workflow(self, reasoner: Reasoner) -> Any:
        """Build the workflow."""

    @abstractmethod
    async def _execute_workflow(
        self, workflow: Any, job: Job
    ) -> WorkflowMessage:
        """Execute the workflow."""
