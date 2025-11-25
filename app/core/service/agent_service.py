from typing import List, Optional

from app.core.agent.agent import AgentConfig
from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.singleton import Singleton
from app.utils.logger import logger


class AgentService(metaclass=Singleton):
    """Leader service with persistence support (Issue #40)"""

    def __init__(self):
        self._leaders: List[Leader] = []
        # Issue #40: DAO for agent persistence
        self._agent_dao: Optional['AgentDao'] = None  # type: ignore

    def set_agent_dao(self, agent_dao: 'AgentDao') -> None:  # type: ignore
        """Set the AgentDao for persistence (Issue #40).

        Args:
            agent_dao: AgentDao instance
        """
        self._agent_dao = agent_dao
        logger.info("AgentDao set for AgentService")

    def set_leadder(self, leader: Leader) -> None:
        """Set the leader. The agent service now manages only one leader."""
        self._leaders = [leader]

    def create_expert(self, expert_config: AgentConfig) -> None:
        """Create an expert and add it to the leader."""
        self.leader.state.create_expert(expert_config)

    def add_expert(self, expert: Expert) -> None:
        """Add an expert to the leader."""
        self.leader.state.add_expert(expert)

    @property
    def leader(self) -> Leader:
        """Get the leader. The agent service now manages only one leader."""
        if len(self._leaders) == 0:
            raise ValueError("No leader found.")
        return self._leaders[0]

    def save_leader(self) -> bool:
        """Save leader configuration to database (Issue #40).

        Returns:
            bool: True if successful, False otherwise
        """
        if not self._agent_dao:
            logger.warning("AgentDao not set, cannot save leader")
            return False

        try:
            if len(self._leaders) > 0:
                self._agent_dao.save_agent_config(self._leaders[0])
                logger.info(f"Saved leader configuration: {self._leaders[0].get_id()}")
                return True
            else:
                logger.warning("No leader to save")
                return False
        except Exception as e:
            logger.error(f"Failed to save leader: {e}")
            return False

    def load_leader(self, leader_config: AgentConfig) -> Leader:
        """Load or create leader with persistence support (Issue #40).

        Tries to load existing leader from database. If not found, creates new one.

        Args:
            leader_config: Default leader configuration (used if no leader in DB)

        Returns:
            Leader: The leader instance
        """
        if not self._agent_dao:
            logger.warning("AgentDao not set, creating leader without persistence")
            leader = Leader(leader_config)
            self.set_leadder(leader)
            return leader

        try:
            # Try to load existing leader from database
            leader_do = self._agent_dao.get_leader()
            if leader_do:
                logger.info(f"Loading existing leader from database: {leader_do.id}")
                config = self._agent_dao.get_agent_config(leader_do.id)
                if config:
                    leader = Leader(config, id=leader_do.id)
                    self.set_leadder(leader)

                    # Set DAO for leader state
                    leader.state.set_agent_dao(self._agent_dao)

                    # Load expert configurations from database
                    leader.state.load_experts_from_db()

                    logger.info(f"Leader loaded successfully with {len(leader.state._expert_configs)} expert configs")
                    return leader

            # No existing leader, create new one
            logger.info("No existing leader found, creating new one")
            leader = Leader(leader_config)
            self.set_leadder(leader)

            # Set DAO for leader state
            leader.state.set_agent_dao(self._agent_dao)

            # Persist new leader
            self._agent_dao.save_agent_config(leader)
            logger.info(f"Created and saved new leader: {leader.get_id()}")

            return leader

        except Exception as e:
            logger.error(f"Failed to load leader: {e}, creating new one")
            leader = Leader(leader_config)
            self.set_leadder(leader)

            # Set DAO for leader state even if loading failed
            if self._agent_dao:
                leader.state.set_agent_dao(self._agent_dao)

            return leader
