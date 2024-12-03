from abc import ABC, abstractmethod

import networkx as nx

from app.agent.workflow.operator.operator import Operator


class Workflow(ABC):
    """Workflow is a sequence of operators that need to be executed"""

    def __init__(self):
        self._operator_graph: nx.DiGraph = nx.DiGraph()
        self._eval_operator: Operator = None

        # self._input_data: str = None

    @abstractmethod
    def execute(self):
        """Execute the workflow."""

    @abstractmethod
    def evaluate(self):
        """Evaluate the workflow."""
