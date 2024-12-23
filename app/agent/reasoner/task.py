from dataclasses import dataclass, field
from typing import List, Optional

from app.agent.job import Job
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.env.insight.insight import Insight
from app.memory.message import WorkflowMessage
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool


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
    """

    # TODO: make the job optional. Now the reasoner memory must use the session_id and job_id to store the memory.
    job: Job
    operator_config: Optional[OperatorConfig] = None
    workflow_messages: Optional[List[WorkflowMessage]] = None
    tools: List[Tool] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    knowledge: str = ""
    insights: Optional[List[Insight]] = None
