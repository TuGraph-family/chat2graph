from app.core.sdk.agentic_service import AgenticService

def load_workflow(optimized_path: str, round_num: int) -> AgenticService:
        workflow_path = optimized_path + f"/round{round_num}" + "/workflow.yml"
        mas = AgenticService.load(workflow_path)
        return mas