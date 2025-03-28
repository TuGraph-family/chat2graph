from typing import List, Optional

from app.core.common.async_func import run_async_function
from app.core.env.insight.insight import Insight
from app.core.model.job import Job
from app.core.model.knowledge import Knowledge
from app.core.model.message import WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.service.toolkit_service import ToolkitService
from app.core.workflow.operator_config import OperatorConfig


class Operator:
    """Operator is a sequence of actions and tools that need to be executed.

    Attributes:
        _id (str): The unique identifier of the operator.
        _config (OperatorConfig): The configuration of the operator.
    """

    def __init__(self, config: OperatorConfig):
        self._config: OperatorConfig = config
        self._toolkit_service: ToolkitService = ToolkitService.instance

    def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        """Execute the operator by LLM client.

        Args:
            reasoner (Reasoner): The reasoner.
            job (Job): The job assigned to the expert.
            workflow_messages (Optional[List[WorkflowMessage]]): The outputs of previous operators.
            previous_expert_outputs (Optional[List[WorkflowMessage]]): The outputs of previous
                experts in workflow message type.
            lesson (Optional[str]): The lesson learned (provided by the successor expert).
        """
        task = self._build_task(
            job=job,
            workflow_messages=workflow_messages,
            previous_expert_outputs=previous_expert_outputs,
            lesson=lesson,
        )

        result = run_async_function(reasoner.infer, task=task)

        return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)

    def _build_task(
        self,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> Task:
        rec_tools, rec_actions = self._toolkit_service.recommend_tools_actions(
            actions=self._config.actions,
            threshold=self._config.threshold,
            hops=self._config.hops,
        )
        merged_workflow_messages: List[WorkflowMessage] = workflow_messages or []
        merged_workflow_messages.extend(previous_expert_outputs or [])
        task = Task(
            job=job,
            operator_config=self._config,
            workflow_messages=merged_workflow_messages,
            tools=rec_tools,
            actions=rec_actions,
            knowledge=self.get_knowledge(job),
            insights=self.get_env_insights(),
            lesson=lesson,
        )
        return task

    def get_knowledge(self, job: Job) -> Knowledge:
        """Get the knowledge from the knowledge base."""
        query = "[JOB TARGET GOAL]:\n" + job.goal + "\n[INPUT INFORMATION]:\n" + job.context
        knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService.instance
        return knowledge_base_service.get_knowledge(query, job.session_id)

    def get_env_insights(self) -> Optional[List[Insight]]:
        """Get the environment information."""
        # TODO: get the environment information
        return None

    def get_id(self) -> str:
        """Get the operator id."""
        return self._config.id
