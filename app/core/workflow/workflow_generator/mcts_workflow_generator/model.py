from pydantic import BaseModel, Field
from typing import Dict, List
from enum import Enum

class Score(BaseModel):
    score: float

class WorkflowLogFormat(BaseModel):
    round_number: int # round{n}
    score: float 
    modifications: List[str] # llm输出
    experience: str
    feedbacks: List[Dict[str, str]] # [{"round_number": xxx, "modificatin": xxx, "experience": xxx, "score": xxx}, ....] 

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