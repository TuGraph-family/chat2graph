from typing import Dict, List, Optional, Tuple

from dbgpt.core.awel import (  # type: ignore
    DAG,
    InputOperator,
    JoinOperator,
    SimpleCallDataInputSource,
)
import networkx as nx  # type: ignore

from app.core.common.async_func import run_async_function
from app.core.model.job import Job
from app.core.model.message import WorkflowMessage
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.workflow import Workflow
from app.plugin.dbgpt.dbgpt_map_operator import DbgptMapOperator


class DbgptWorkflow(Workflow):
    """DB-GPT workflow"""

    def __init__(self):
        self._tail_map_op: Optional[DbgptMapOperator] = None
        super().__init__()

    def _build_workflow(self, reasoner: Reasoner) -> DbgptMapOperator:
        """Build the DB-GPT workflow."""
        if self._operator_graph.number_of_nodes() == 0:
            raise ValueError("There is no operator in the workflow.")

        def _merge_workflow_messages(*args) -> Tuple[Job, List[WorkflowMessage], Optional[str]]:
            """Combine the ouputs from the previous MapOPs and the InputOP."""
            job: Optional[Job] = None
            workflow_messages: List[WorkflowMessage] = []
            lesson: Optional[str] = None

            for arg in args:
                if isinstance(arg, tuple):
                    for item in arg:
                        if isinstance(item, Job):
                            job = item
                        elif isinstance(item, list):
                            if all(isinstance(i, WorkflowMessage) for i in item):
                                workflow_messages.extend(item)
                            else:
                                raise ValueError(
                                    "Unknown data type in workflow message list: "
                                    f"{', '.join(str(type(i)) for i in item)}"
                                )
                        elif isinstance(item, str):
                            lesson = item
                        elif item is not None:
                            raise ValueError(f"Unknown data type in tuple: {type(item)}")
                elif isinstance(arg, WorkflowMessage):
                    workflow_messages.append(arg)
                else:
                    raise ValueError(f"Unknown data type: {type(arg)}")

            if not job:
                raise ValueError("No job provided in the workflow.")

            return job, workflow_messages, lesson

        with DAG("dbgpt_workflow"):
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
                n for n in self._operator_graph.nodes() if self._operator_graph.out_degree(n) == 0
            ]
            assert len(tail_map_op_ids) == 1, "The workflow should have only one tail operator."
            _tail_map_op: DbgptMapOperator = map_ops[tail_map_op_ids[0]]

            # fourth step: add the eval operator at the end of the DAG
            if self._evaluator:
                eval_map_op = DbgptMapOperator(operator=self._evaluator, reasoner=reasoner)
                join_op = JoinOperator(combine_function=_merge_workflow_messages)

                _tail_map_op >> join_op
                input_op >> join_op
                join_op >> eval_map_op

                self._tail_map_op = eval_map_op
            else:
                self._tail_map_op = _tail_map_op

            return self._tail_map_op

    def _execute_workflow(
        self,
        workflow: DbgptMapOperator,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        """Execute the workflow."""
        return run_async_function(workflow.call, call_data=(job, workflow_messages, lesson))
