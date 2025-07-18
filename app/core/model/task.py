from dataclasses import dataclass, field
from typing import List, Optional

from app.core.env.insight.insight import Insight
from app.core.model.file_descriptor import FileDescriptor
from app.core.model.job import Job
from app.core.model.knowledge import Knowledge
from app.core.model.message import WorkflowMessage
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.workflow.operator_config import OperatorConfig


@dataclass
class ToolCallContext:
    """Context for tool call execution.

    Attributes:
        job_id: The job ID associated with the tool call.
        operator_id: The operator ID associated with the tool call.
    """

    job_id: str
    operator_id: str


@dataclass
class Task:
    """Task in the system.

    Attributes:
        job (Job): The job assigned to the expert.
        operator_config (OperatorConfig): The configuration of the operator.
        workflow_messages (List[WorkflowMessage]): The workflow messages.
        tools (List[Action]): The tools recommended by the toolkit for the operator.
        actions (List[Action]): The actions recommended by the toolkit for the operator.
        knowledge (Optional[Knowledge]): The knowledge from the knowledge base.
        insights (Optional[List[Insight]]): The insights from the environment.
        lesson (Optional[str]): The lesson learned from the job execution.
        file_descriptors (Optional[List[FileDescriptor]]): The file descriptors.
    """

    job: Job
    operator_config: Optional[OperatorConfig] = None
    workflow_messages: Optional[List[WorkflowMessage]] = None
    tools: List[Tool] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    knowledge: Optional[Knowledge] = None
    insights: Optional[List[Insight]] = None
    lesson: Optional[str] = None
    file_descriptors: Optional[List[FileDescriptor]] = None

    def get_tool_call_ctx(self) -> ToolCallContext:
        """Get the function call context for the task."""
        return ToolCallContext(
            job_id=self.job.id,
            operator_id=self.operator_config.id if self.operator_config else "unknown_operator_id",
        )
