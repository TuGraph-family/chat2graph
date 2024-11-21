from abc import ABC, abstractmethod

import networkx as nx

from app.agent.workflow.operator.operator import Operator


class Workflow(ABC):
    """A workflow is a sequence of operators that need to be executed"""

    def __init__(self):
        self.operator_graph: nx.DiGraph = nx.DiGraph()
        self.eval_operator: Operator = None

        self.input_data: str = None

    @abstractmethod
    def execute(self):
        """Execute the workflow."""

    @abstractmethod
    def evaluate(self):
        """Evaluate the workflow."""


class DbgptWorkflow(Workflow):
    """DB-GPT workflow"""

    def execute(self):
        """Execute the workflow."""

    def evaluate(self):
        """Evaluate the workflow."""
