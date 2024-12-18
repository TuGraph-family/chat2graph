from dataclasses import dataclass
from typing import List, Optional

from app.agent.job import Job
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.env.insight.insight import Insight
from app.memory.message import WorkflowMessage
from app.toolkit.tool.tool import Tool


@dataclass
class Task:
    """Task in the system.

    Attributes:
        job (Job): The job assigned to the experts.
        operator_config (OperatorConfig): The configuration of the operator.
        workflow_messages (List[WorkflowMessage]): The workflow messages.
        tools (List[Tool]): The tools can be used by the reasoner.
        action_rels (str): The action relationships defined in the operator.
        knowledge (str): The knowledge from the knowledge base.
        insights (List[Insight]): The insights from the environment.
    """

    # TODO: make the job optional. Now the reasoner memory must use the session_id and job_id to store the memory.
    job: Job
    operator_config: Optional[OperatorConfig] = None
    workflow_messages: Optional[List[WorkflowMessage]] = None
    tools: Optional[List[Tool]] = None
    # TODO: action can be related to a tool, move action_rels to action's previous / next fields.
    action_rels: str = ""
    knowledge: str = ""
    insights: Optional[List[Insight]] = None
