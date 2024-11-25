from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import networkx as nx  # type: ignore
from dbgpt.core.awel import (  # type: ignore
    DAG,
    InputOperator,
    JoinOperator,
    SimpleInputSource,
)

from app.agent.workflow.operator.dbgpt_operator import DbgptMapOperator
from app.agent.workflow.operator.operator import Operator


class Workflow(ABC):
    """Workflow is a sequence of operators that need to be executed"""

    def __init__(self):
        self._operator_graph: nx.DiGraph = nx.DiGraph()
        self._eval_operator: Optional[Operator] = None

    @abstractmethod
    async def execute(self):
        """Execute the workflow."""

    @abstractmethod
    async def evaluate(self):
        """Evaluate the workflow."""


class DbgptWorkflow(Workflow):
    """DB-GPT workflow

    Attributes:
        _operator_graph (nx.DiGraph): The operator graph of the workflow.
        _dbgpt_flow (None): The DB-GPT flow.

        _operator_graph schema:
        {
            "operator_id": {
                "operator": Operator,
                "converted_operator": BaseOperator(DB-GPT)
            }
        }
    """

    def __init__(
        self,
        operator_graph: nx.DiGraph = nx.DiGraph(),
        input_data: Optional[str] = None,
    ):
        super().__init__()
        self._operator_graph: nx.DiGraph = operator_graph
        self._dbgpt_flow: DAG = None
        self._input_data: str = input_data or ""

    async def execute(self):
        """Execute the workflow."""
        tail_map_op = self.buildin_workflow()

        return await tail_map_op.call(call_data=self._input_data)

    async def evaluate(self):
        """Evaluate the workflow."""

    def add_operator(
        self,
        operator: Operator,
        previous_ops: Optional[List[Operator]] = None,
        next_ops: Optional[List[Operator]] = None,
    ):
        """Add an operator to the workflow."""
        self._operator_graph.add_node(operator.id, operator=operator)
        if previous_ops:
            for previous_op in previous_ops:
                # if previous_op not in self._operator_graph.nodes:
                if previous_op.id not in self._operator_graph.nodes:
                    self._operator_graph.add_node(previous_op.id, operator=previous_op)
                self._operator_graph.add_edge(previous_op.id, operator.id)
        if next_ops:
            for next_op in next_ops:
                if next_op.id not in self._operator_graph.nodes:
                    self._operator_graph.add_node(next_op.id, operator=next_op)
                self._operator_graph.add_edge(operator.id, next_op.id)

    def remove_operator(self, operator: Operator):
        """Remove an operator from the workflow."""
        self._operator_graph.remove_node(operator.id)

    def buildin_workflow(self) -> DbgptMapOperator:
        """Build-in the DB-GPT workflow."""
        if self._dbgpt_flow:
            raise ValueError("The DB-GPT workflow has been built-in.")

        with DAG("dbgpt_workflow") as dag:
            input_op = InputOperator(
                input_source=SimpleInputSource(data=self._input_data)
            )

            map_ops: Dict[str, DbgptMapOperator] = {}  # op_id -> map_op

            # first pass: convert all original operators to MapOPs
            for op_id in self._operator_graph.nodes():
                base_op = self._operator_graph.nodes[op_id]["operator"]
                map_ops[op_id] = DbgptMapOperator(base_op)

            # second pass: insert JoinOPs between MapOPs
            for op_id in nx.topological_sort(self._operator_graph):
                current_op = map_ops[op_id]
                in_edges = list(self._operator_graph.in_edges(op_id))

                if in_edges:

                    def combine_function(*args) -> Dict[str, str]:
                        combined_data: Dict[str, str] = {}
                        scratchpads: List[str] = []

                        for arg in args:
                            if isinstance(arg, dict):
                                if scratchpad := arg.get("scratchpad"):
                                    scratchpads.append(scratchpad)
                                combined_data.update({
                                    k: v for k, v in arg.items() if k != "scratchpad"
                                })

                        if len(scratchpads) == 1:
                            combined_data["scratchpad"] = scratchpads[0]
                        else:
                            combined_data["scratchpad"] = "\n".join(
                                f"[{i + 1}]\n{pad}" for i, pad in enumerate(scratchpads)
                            )

                        return combined_data

                    join_op = JoinOperator(combine_function=combine_function)

                    # connect all previous MapOPs to JoinOP
                    for src_id, _ in in_edges:
                        map_ops[src_id] >> join_op

                    input_op >> join_op

                    # connect the JoinOP to the current MapOP
                    join_op >> current_op
                else:
                    # if no previous MapOPs, connect the InputOP to the current MapOP
                    input_op >> current_op

            self._dbgpt_flow = dag

            tail_map_op_id = next(
                n
                for n in self._operator_graph.nodes()
                if self._operator_graph.out_degree(n) == 0
            )
            tail_map_op = map_ops[tail_map_op_id]

            return tail_map_op
