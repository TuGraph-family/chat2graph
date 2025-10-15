from enum import Enum
from typing import Dict, List, Literal

from pydantic import BaseModel


class OptimizeActionType(str, Enum):
    ADD = "add"
    # DELETE = "delete an operator or expert"
    MODIFY = "modify"


class OptimizeObject(str, Enum):
    OPERATOR = "operator"
    EXPERT = "expert"


class OptimizeAction(BaseModel):
    action_type: OptimizeActionType
    optimize_object: OptimizeObject
    reason: str


class WorkflowLogFormat(BaseModel):
    round_number: int  # round{n}
    score: float
    optimize_suggestions: List[OptimizeAction] = []
    modifications: List[str]  # llm输出
    reflection: str
    feedbacks: List[
        Dict[str, str]
    ]  # [{"round_number": xxx, "modificatin": xxx, "experience": xxx, "score": xxx}, ....]


class OptimizeResp(BaseModel):
    modifications: List[str]
    new_configs: Dict[str, str]


class AgenticConfigSection(Enum):
    APP = "app"
    PLUGIN = "plugin"
    REASONER = "reasoner"
    TOOLS = "tools"
    ACTIONS = "actions"
    TOOLKIT = "toolkit"
    OPERATORS = "operators"
    EXPERTS = "experts"
    LEADER = "leader"
    KNOWLEDGEBASE = "knowledgebase"
    MEMORY = "memory"
    ENV = "env"


class ExecuteResult(BaseModel):
    task: str
    verifier: str
    model_output: str
    ori_score: float
    score: float
    error: str
    succeed: Literal["yes", "no", "unknown"]


class ReflectResult(BaseModel):
    failed_reason: List[str]
    optimize_suggestion: List[str]
