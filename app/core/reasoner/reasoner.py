from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.model.task import Task
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.mcp_tool import McpTool


class Reasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

    def __init__(self):
        self._memories: Dict[
            str, Dict[str, Dict[str, ReasonerMemory]]
        ] = {}  # session_id -> job_id -> operator_id -> memory

    async def infer(self, task: Task) -> str:
        """Infer by the reasoner with cleanup."""
        try:
            return await self._infer(task)
        finally:
            # close the MCP tools if they are used in the task
            toolkit_service: ToolkitService = ToolkitService.instance
            mcp_tools: List[McpTool] = [tool for tool in task.tools if isinstance(tool, McpTool)]
            await toolkit_service.close_mcp_tools(mcp_tools=mcp_tools)

    @abstractmethod
    async def _infer(self, task: Task) -> str:
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
