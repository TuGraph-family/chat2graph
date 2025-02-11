from dataclasses import dataclass, field
from typing import List, Optional

from app.core.model.job import Job
from app.core.workflow.operator_config import OperatorConfig
from app.core.env.insight.insight import Insight
from app.core.model.message import WorkflowMessage
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool


@dataclass
class Task:
    """Task in the system.

    Attributes:
        job (Job): The job assigned to the experts.
        operator_config (OperatorConfig): The configuration of the operator.
        workflow_messages (List[WorkflowMessage]): The workflow messages.
        tools (List[Action]): The tools recommended by the toolkit for the operator.
        actions (List[Action]): The actions recommended by the toolkit for the operator.
        knowledge (str): The knowledge from the knowledge base.
        insights (List[Insight]): The insights from the environment.
        lesson (str): The lesson learned from the job execution.
    """

    # TODO: make the job optional. Now the reasoner memory must use the session_id and
    # job_id to store the memory.
    job: Job
    operator_config: Optional[OperatorConfig] = None
    workflow_messages: Optional[List[WorkflowMessage]] = None
    tools: List[Tool] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    knowledge: str = ""
    insights: Optional[List[Insight]] = None
    lesson: Optional[str] = None
