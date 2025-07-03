from abc import ABC, abstractmethod
from typing import Any, Dict

from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.model.task import Task
from app.core.prompt.model_service import TASK_DESCRIPTOR_PROMPT_TEMPLATE


class Reasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

    def __init__(self):
        self._memories: Dict[
            str, Dict[str, Dict[str, ReasonerMemory]]
        ] = {}  # session_id -> job_id -> operator_id -> memory

    @abstractmethod
    async def infer(self, task: Task) -> str:
        """Infer by the reasoner."""

    @abstractmethod
    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""

    @abstractmethod
    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process."""

    @abstractmethod
    async def conclude(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclude the inference results."""

    @abstractmethod
    def init_memory(self, task: Task) -> ReasonerMemory:
        """Initialize the memory."""

    @abstractmethod
    def get_memory(self, task: Task) -> ReasonerMemory:
        """Get the memory."""

    def _build_task_context(self, task: Task) -> str:
        """Build the task context string for system prompts."""
        if task.insights:
            env_info = "\n".join([f"{insight}" for insight in task.insights])
        else:
            env_info = "No environment information provided in this round."
        if task.workflow_messages:
            previous_input = "\n".join(
                [f"{workflow_message.scratchpad}" for workflow_message in task.workflow_messages]
            )
        else:
            previous_input = "No previous input provided in this round."
        action_rels = "\n".join(
            [f"[action {action.name}: {action.description}] -next-> " for action in task.actions]
        )
        file_desc = (
            "\n".join(
                f"File name: {f.name} - File id: {f.id}" for f in (task.file_descriptors or [])
            )
            or "No files provided in this round."
        )

        return TASK_DESCRIPTOR_PROMPT_TEMPLATE.format(
            action_rels=action_rels,
            context=task.job.goal + task.job.context,
            session_id=task.job.session_id,
            job_id=task.job.id,
            file_descriptors=file_desc,
            env_info=env_info,
            knowledge=task.knowledge.get_payload() if task.knowledge else "",
            previous_input=previous_input,
            lesson=task.lesson or "No lesson learned in this round.",
        )

    def _build_func_description(self, task: Task) -> str:
        """Build the function description string for system prompts."""
        if len(task.tools) > 0:
            return "\n".join(
                [
                    f"({i + 1}) Function {tool.name}():\n\t{tool.description}\n"
                    for i, tool in enumerate(task.tools)
                ]
            )
        return "No function calling in this round."
