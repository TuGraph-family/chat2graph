from typing import List, Dict, Optional

from app.core.agent.agent import AgentConfig
from app.core.agent.expert import Expert
from app.core.agent.leader_state import LeaderState
from app.utils.logger import logger


class BuiltinLeaderState(LeaderState):
    """Builtin leader state with persistence support .

    attributes:
        _expert_instances (Dict[str, Expert]): it stores the expert agent instances.
        _expert_creation_lock (threading.Lock): it is used to lock the expert creation.
        _expert_configs (Dict[str, AgentConfig]): cached expert configurations from database.
    """

    def __init__(self):
        super().__init__()
        #  Cache for expert configurations loaded from database
        self._expert_configs: Dict[str, AgentConfig] = {}

    def get_expert_by_name(self, expert_name: str) -> Expert:
        """Get existing expert instance."""
        # get expert ID by expert name
        for expert in self._expert_instances.values():
            if expert.get_profile().name == expert_name:
                return expert
        raise ValueError(f"Expert {expert_name} not exists in the leader state.")

    def get_expert_by_id(self, expert_id: str) -> Expert:
        """Get existing expert instance with lazy loading ."""
        # 1. Check memory cache first
        if expert_id in self._expert_instances:
            return self._expert_instances[expert_id]

        # 2. Try to load from configuration cache
        if expert_id in self._expert_configs:
            logger.info(f"Lazy loading expert from config cache: {expert_id}")
            config = self._expert_configs[expert_id]
            expert = Expert(agent_config=config, id=expert_id)
            self._expert_instances[expert_id] = expert
            return expert

        # 3. Try to load from database
        if self._agent_dao:
            try:
                logger.info(f"Lazy loading expert from database: {expert_id}")
                config = self._agent_dao.get_agent_config(expert_id)
                if config:
                    expert = Expert(agent_config=config, id=expert_id)
                    self._expert_instances[expert_id] = expert
                    self._expert_configs[expert_id] = config
                    return expert
            except Exception as e:
                logger.error(f"Failed to load expert {expert_id} from database: {e}")

        # 4. Not found
        raise KeyError(f"Expert {expert_id} not found")

    def list_experts(self) -> List[Expert]:
        """Return a list of all registered expert information."""
        return list(self._expert_instances.values())

    def create_expert(self, agent_config: AgentConfig) -> Expert:
        """Add an expert profile to the registry with persistence ."""
        with self._expert_creation_lock:
            expert_name = agent_config.profile.name

            # Check if expert with same name already exists in database
            if self._agent_dao:
                try:
                    existing_do = self._agent_dao.get_agent_by_name(expert_name)
                    if existing_do:
                        expert_id = existing_do.id
                        logger.info(f"Expert {expert_name} already exists with ID: {expert_id}")
                        # Check if already in memory
                        if expert_id in self._expert_instances:
                            return self._expert_instances[expert_id]
                        # Load from database
                        config = self._agent_dao.get_agent_config(expert_id)
                        if config:
                            expert = Expert(agent_config=config, id=expert_id)
                            self._expert_instances[expert_id] = expert
                            self._expert_configs[expert_id] = config
                            return expert
                except Exception as e:
                    logger.warning(f"Failed to check existing expert: {e}")

            # Create new expert
            expert = Expert(agent_config=agent_config)
            expert_id = expert.get_id()

            # Persist to database
            if self._agent_dao:
                try:
                    self._agent_dao.save_agent_config(expert)
                    logger.info(f"Persisted expert {expert_name} with ID: {expert_id}")
                except Exception as e:
                    logger.error(f"Failed to persist expert {expert_name}: {e}")

            # Cache in memory
            self._expert_instances[expert_id] = expert
            self._expert_configs[expert_id] = agent_config

            return expert

    def add_expert(self, expert: Expert) -> None:
        """Add the expert"""
        self._expert_instances[expert.get_id()] = expert

    def remove_expert(self, expert_id: str) -> None:
        """Remove the expert"""
        self._expert_instances.pop(expert_id, None)

    def load_experts_from_db(self) -> None:
        """Load expert configurations from database .

        This loads all expert configurations from the database and caches them.
        Actual Expert instances are created lazily when accessed via get_expert_by_id.
        """
        if not self._agent_dao:
            logger.warning("AgentDao not set, skipping expert loading from database")
            return

        try:
            expert_dos = self._agent_dao.list_experts(active_only=True)
            logger.info(f"Loading {len(expert_dos)} expert configurations from database")

            for expert_do in expert_dos:
                try:
                    config = self._agent_dao.get_agent_config(expert_do.id)
                    if config:
                        self._expert_configs[expert_do.id] = config
                        logger.debug(f"Cached configuration for expert: {expert_do.name}")
                except Exception as e:
                    logger.error(f"Failed to load expert config {expert_do.id}: {e}")

            logger.info(f"Successfully cached {len(self._expert_configs)} expert configurations")

        except Exception as e:
            logger.error(f"Failed to load experts from database: {e}")
