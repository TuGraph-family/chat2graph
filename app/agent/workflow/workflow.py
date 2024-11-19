import networkx as nx

from app.agent.workflow.operator.operator import Operator


class Workflow:
    """A workflow is a sequence of operators that need to be executed"""

    def __init__(self):
        self.operator_graph: nx.DiGraph = nx.DiGraph()
        self.eval_operator: Operator = None

        self.input_data: str = None

    def execute(self):
        """Execute the workflow."""

    def evaluate(self):
        """Evaluate the workflow."""
