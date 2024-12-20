from typing import Dict, List, Optional, Tuple

import networkx as nx  # type: ignore
from dbgpt.core.awel import (  # type: ignore
    DAG,
    InputOperator,
    JoinOperator,
    SimpleCallDataInputSource,
)

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.workflow import Workflow
from app.memory.message import WorkflowMessage
from app.plugin.dbgpt.dbgpt_map_operator import DbgptMapOperator


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

    def __init__(self, eval_operator: Optional[Operator] = None):
        super().__init__(eval_operator=eval_operator)
        self._dbgpt_flow: Optional[DAG] = None
        self._tail_map_op: Optional[DbgptMapOperator] = None

    async def execute(self, job: Job, reasoner: Reasoner) -> WorkflowMessage:
        """Execute the workflow.

        Args:
            job (Job): The job assigned to the agent.
            reasoner (Reasoner): The reasoner that reasons the operators.

        Returns:
            WorkflowMessage: The output of the workflow.
        """
        if not self._dbgpt_flow or not self._tail_map_op:
            self.build_workflow(reasoner=reasoner)

        assert self._dbgpt_flow and self._tail_map_op, (
            "The DB-GPT workflow is not built-in."
        )
        return await self._tail_map_op.call(call_data=job)

    def add_operator(
        self,
        operator: Operator,
        previous_ops: Optional[List[Operator]] = None,
        next_ops: Optional[List[Operator]] = None,
    ):
        """Add an operator to the workflow."""
        self._operator_graph.add_node(operator.get_id(), operator=operator)
        if previous_ops:
            for previous_op in previous_ops:
                if not self._operator_graph.has_node(previous_op.get_id()):
                    self._operator_graph.add_node(
                        previous_op.get_id(), operator=previous_op
                    )
                self._operator_graph.add_edge(previous_op.get_id(), operator.get_id())
        if next_ops:
            for next_op in next_ops:
                if not self._operator_graph.has_node(next_op.get_id()):
                    self._operator_graph.add_node(next_op.get_id(), operator=next_op)
                self._operator_graph.add_edge(operator.get_id(), next_op.get_id())

    def remove_operator(self, operator: Operator) -> None:
        """Remove an operator from the workflow."""
        self._operator_graph.remove_node(operator.get_id())

    def build_workflow(self, reasoner: Reasoner) -> None:
        """Build the DB-GPT workflow."""
        if self._operator_graph.number_of_nodes() == 0:
            raise ValueError("There is no operator in the workflow.")
        if self._dbgpt_flow or self._tail_map_op:
            raise ValueError("The DB-GPT workflow has been built-in.")

        def _merge_workflow_messages(*args) -> Tuple[Job, List[WorkflowMessage]]:
            """Combine the ouputs from the previous MapOPs and the InputOP."""
            job: Optional[Job] = None
            workflow_messsages: List[WorkflowMessage] = []

            for arg in args:
                if isinstance(arg, Job):
                    job = arg
                elif isinstance(arg, WorkflowMessage):
                    workflow_messsages.append(arg)
                else:
                    raise ValueError(f"Unknown data type: {type(arg)}")

            if not job:
                raise ValueError("No job provided in the workflow.")

            return job, workflow_messsages

        with DAG("dbgpt_workflow") as dag:
            input_op = InputOperator(input_source=SimpleCallDataInputSource())
            map_ops: Dict[str, DbgptMapOperator] = {}  # op_id -> map_op

            # first step: convert all original operators to MapOPs
            for op_id in self._operator_graph.nodes():
                base_op = self._operator_graph.nodes[op_id]["operator"]
                map_ops[op_id] = DbgptMapOperator(operator=base_op, reasoner=reasoner)

            # second step: insert JoinOPs between MapOPs
            for op_id in nx.topological_sort(self._operator_graph):
                current_op: DbgptMapOperator = map_ops[op_id]
                in_edges = list(self._operator_graph.in_edges(op_id))

                if in_edges:
                    join_op = JoinOperator(combine_function=_merge_workflow_messages)

                    # connect all previous MapOPs to JoinOP
                    for src_id, _ in in_edges:
                        map_ops[src_id] >> join_op

                    input_op >> join_op

                    # connect the JoinOP to the current MapOP
                    join_op >> current_op
                else:
                    # if no previous MapOPs, connect the InputOP to the current MapOP
                    input_op >> current_op

            # third step: get the tail of the workflow which contains the operators
            tail_map_op_ids = [
                n
                for n in self._operator_graph.nodes()
                if self._operator_graph.out_degree(n) == 0
            ]
            assert len(tail_map_op_ids) == 1, (
                "The workflow should have only one tail operator."
            )
            _tail_map_op: DbgptMapOperator = map_ops[tail_map_op_ids[0]]

            # fourth step: add the eval operator at the end of the DAG
            if self._eval_operator:
                eval_map_op = DbgptMapOperator(
                    operator=self._eval_operator, reasoner=reasoner
                )
                join_op = JoinOperator(combine_function=_merge_workflow_messages)

                _tail_map_op >> join_op
                input_op >> join_op
                join_op >> eval_map_op
                _tail_map_op = eval_map_op

                self._tail_map_op = eval_map_op
            else:
                self._tail_map_op = _tail_map_op

            self._dbgpt_flow = dag

    def get_operator(self, operator_id: str) -> Optional[Operator]:
        """Get an operator from the workflow."""
        return None

    def get_operators(self) -> List[Operator]:
        """Get all operators from the workflow."""
        return []

    def visualize(self) -> None:
        """Visualize the workflow."""
