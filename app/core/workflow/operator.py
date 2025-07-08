from typing import List, Optional, cast

from app.core.env.insight.insight import Insight
from app.core.model.file_descriptor import FileDescriptor
from app.core.model.job import Job, SubJob
from app.core.model.knowledge import Knowledge
from app.core.model.message import FileMessage, HybridMessage, MessageType, WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.service.file_service import FileService
from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.service.message_service import MessageService
from app.core.service.tool_connection_service import ToolConnectionService
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

    async def execute(
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

        # infer by the reasoner
        result = await reasoner.infer(task=task)

        # destroy MCP connections for the operator
        tool_connection_service: ToolConnectionService = ToolConnectionService.instance
        await tool_connection_service.release_connection(call_tool_ctx=task.get_tool_call_ctx())

        return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)

    def _build_task(
        self,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> Task:
        toolkit_service: ToolkitService = ToolkitService.instance
        file_service: FileService = FileService.instance
        message_service: MessageService = MessageService.instance

        rec_tools, rec_actions = toolkit_service.recommend_tools_actions(
            actions=self._config.actions,
            threshold=self._config.threshold,
            hops=self._config.hops,
        )

        merged_workflow_messages: List[WorkflowMessage] = workflow_messages or []
        merged_workflow_messages.extend(previous_expert_outputs or [])

        # get the file descriptors, to provide some way of an access to the content of the files
        file_descriptors: List[FileDescriptor] = []
        if isinstance(job, SubJob):
            original_job_id: Optional[str] = job.original_job_id
            assert original_job_id is not None, "SubJob must have an original job id"
        else:
            original_job_id = job.id
        hybrid_messages: List[HybridMessage] = cast(
            List[HybridMessage],
            message_service.get_message_by_job_id(
                job_id=original_job_id, message_type=MessageType.HYBRID_MESSAGE
            ),
        )
        for hybrid_message in hybrid_messages:
            # get the file descriptors from the hybrid message
            attached_messages = hybrid_message.get_attached_messages()
            for attached_message in attached_messages:
                if isinstance(attached_message, FileMessage):
                    file_descriptor = file_service.get_file_descriptor(
                        file_id=attached_message.get_file_id()
                    )
                    file_descriptors.append(file_descriptor)

        task = Task(
            job=job,
            operator_config=self._config,
            workflow_messages=merged_workflow_messages,
            tools=rec_tools,
            actions=rec_actions,
            knowledge=self.get_knowledge(job),
            insights=self.get_env_insights(),
            lesson=lesson,
            file_descriptors=file_descriptors,
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
