from pydantic import BaseModel, Field


class Score(BaseModel):
    score: float

class WorkflowLogFormat(BaseModel):
    round_number: int # round{n}
    score: float 
    modification: str # llm输出
    experience: str
    feedbacks: list[dict[str, str]] # [{"round_number": xxx, "modificatin": xxx, "experience": xxx, "score": xxx}, ....] 

class OptimizeResp(BaseModel):
    modification: str = Field(description="The modification of current round.")
    workflow: str = Field(description="The configuration of the workflow.")