from abc import ABC, abstractmethod
import threading
from typing import Dict, List, Optional, TYPE_CHECKING

from app.core.agent.agent import AgentConfig
from app.core.agent.expert import Expert

if TYPE_CHECKING:
    from app.core.dal.dao.agent_dao import AgentDao


class LeaderState(ABC):
    """Leader state manages agents' landscape.

    attributes:
        _expert_instances (Dict[str, Expert]): it stores the expert agent instances.
        _expert_creation_lock (threading.Lock): it is used to lock the expert creation.
        _agent_dao (Optional[AgentDao]): DAO for agent persistence.
    """

    def __init__(self):
        self._expert_instances: Dict[str, Expert] = {}  # expert_id -> instance
        self._expert_creation_lock: threading.Lock = threading.Lock()
        # DAO for agent persistence
        self._agent_dao: Optional['AgentDao'] = None

    @abstractmethod
    def get_expert_by_name(self, expert_name: str) -> Expert:
        """Get existing expert instance or create a new one."""

    @abstractmethod
    def get_expert_by_id(self, expert_id: str) -> Expert:
        """Get existing expert instance or create a new one."""

    @abstractmethod
    def list_experts(self) -> List[Expert]:
        """Return a list of all registered expert information."""

    @abstractmethod
    def create_expert(self, agent_config: AgentConfig) -> Expert:
        """Add an expert profile to the registry."""

    @abstractmethod
    def add_expert(self, expert: Expert) -> None:
        """Add the expert"""

    @abstractmethod
    def remove_expert(self, expert_id: str) -> None:
        """Remove the expert"""

    def set_agent_dao(self, agent_dao: 'AgentDao') -> None:
        """Set the AgentDao for persistence.

        Args:
            agent_dao: AgentDao instance for database operations
        """
        self._agent_dao = agent_dao

    def load_experts_from_db(self) -> None:
        """Load expert configurations from database.

        This method should be implemented by subclasses to load
        expert configurations from the database and cache them.
        Actual Expert instances are created lazily when needed.
        """
        pass  # Subclasses can override if needed
