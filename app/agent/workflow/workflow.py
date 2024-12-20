from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import networkx as nx  # type: ignore

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator
from app.commom.type import WorkflowStatus
from app.memory.message import WorkflowMessage


@dataclass
class WorkflowResult:
    """Execution result of the workflow.

    Attributes:
        job_id (str): The unique identifier of the job.
        status (str): The status of the job.
        output (WorkflowMessage): The output of the job.
        error (Optional[Exception]): The error of the job.
        job_execution_context (Dict[str, str]): The context of the job.
        experience (Optional[str]): The experience of the job and the lessons learned.
    """

    job_id: str
    status: WorkflowStatus = WorkflowStatus.SUCCESS
    output: WorkflowMessage = WorkflowMessage(content={"scratchpad": ""})
    # TODO: remove error and job_execution_context
    error: Optional[Exception] = None
    job_execution_context: Dict[str, str] = field(default_factory=dict)
    experience: Optional[str] = None


class Workflow(ABC):
    """Workflow is a sequence of operators that need to be executed

    Attributes:
        _operator_graph (nx.DiGraph): The operator graph of the workflow.
        _eval_operator (Optional[Operator]): The operator to evaluate the progress of the workflow.
    """

    def __init__(
        self,
        operator_graph: Optional[nx.DiGraph] = None,
        eval_operator: Optional[Operator] = None,
    ):
        self._operator_graph: nx.DiGraph = operator_graph or nx.DiGraph()
        self._eval_operator: Optional[Operator] = eval_operator

    @abstractmethod
    def build_workflow(self, reasoner: Reasoner) -> None:
        """Build in the workflow."""

    @abstractmethod
    async def execute(self, job: Job, reasoner: Reasoner) -> WorkflowMessage:
        """Execute the workflow."""

    @abstractmethod
    def add_operator(
        self,
        operator: Operator,
        previous_ops: Optional[List[Operator]] = None,
        next_ops: Optional[List[Operator]] = None,
    ):
        """Add an operator to the workflow."""

    @abstractmethod
    def remove_operator(self, operator: Operator) -> None:
        """Remove an operator from the workflow."""

    @abstractmethod
    def get_operator(self, operator_id: str) -> Optional[Operator]:
        """Get an operator from the workflow."""

    @abstractmethod
    def get_operators(self) -> List[Operator]:
        """Get all operators from the workflow."""

    @abstractmethod
    def visualize(self) -> None:
        """Visualize the workflow."""
