"""Agent Data Access Object.

Provides CRUD operations and configuration reconstruction for Agent persistence.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.dal.dao.dao import Dao
from app.core.dal.do.agent_do import AgentDo
from app.core.agent.agent import Agent, AgentConfig, Profile
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.workflow import Workflow
from app.utils.logger import logger


class AgentDao(Dao[AgentDo]):
    """Agent Data Access Object.

    Provides persistence, query, and reconstruction functionality for Agent configuration.

    Attributes:
        model_class: AgentDo data model class
        session: SQLAlchemy session
    """

    def __init__(self, session: Session):
        """Initialize AgentDao.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(AgentDo, session)

    # ==================== Save Methods ====================

    def save_agent_config(self, agent: Agent) -> AgentDo:
        """Save Agent configuration to database.

        Extract configuration from Agent instance and persist it.
        If agent already exists (by ID), update; otherwise create new record.

        Args:
            agent: Agent instance

        Returns:
            AgentDo: Saved data object

        Example:
            >>> from app.core.agent.expert import Expert
            >>> agent_dao = AgentDao(session)
            >>> expert = Expert(agent_config)
            >>> agent_do = agent_dao.save_agent_config(expert)
        """
        try:
            # Check if already exists
            existing = self.get_by_id(agent._id)

            # Extract configuration
            config_data = self._extract_agent_config(agent)

            if existing:
                # Update existing record
                logger.info(f"Updating existing agent config: {agent._id}")
                self.update(agent._id, **config_data)
                return self.get_by_id(agent._id)
            else:
                # Create new record
                logger.info(f"Creating new agent config: {agent._id}")
                config_data["id"] = agent._id
                return self.create(**config_data)

        except Exception as e:
            logger.error(f"Failed to save agent config: {e}")
            raise

    def _extract_agent_config(self, agent: Agent) -> Dict[str, Any]:
        """Extract configuration from Agent instance.

        Args:
            agent: Agent instance

        Returns:
            Configuration dictionary
        """
        # Determine agent type
        from app.core.agent.leader import Leader
        agent_type = "leader" if isinstance(agent, Leader) else "expert"

        config_data = {
            "agent_type": agent_type,
            "name": agent._profile.name,
            "description": agent._profile.description,
            "reasoner_type": agent._reasoner.__class__.__name__,
            "reasoner_config": self._extract_reasoner_config(agent._reasoner),
            "workflow_type": agent._workflow.__class__.__name__,
            "workflow_config": self._extract_workflow_config(agent._workflow),
        }

        # Leader specific configuration
        if agent_type == "leader" and hasattr(agent, '_leader_state'):
            config_data["leader_state_type"] = agent._leader_state.__class__.__name__

        return config_data

    # ==================== Query Methods ====================

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get Agent configuration and rebuild AgentConfig.

        Read configuration from database and build AgentConfig object for Agent reconstruction.

        Args:
            agent_id: Agent ID

        Returns:
            AgentConfig or None (if not exists)

        Example:
            >>> agent_dao = AgentDao(session)
            >>> config = agent_dao.get_agent_config("agent-123")
            >>> if config:
            ...     from app.core.agent.expert import Expert
            ...     agent = Expert(config, id="agent-123")
        """
        try:
            agent_do = self.get_by_id(agent_id)
            if not agent_do:
                logger.warning(f"Agent config not found: {agent_id}")
                return None

            return self._build_agent_config(agent_do)

        except Exception as e:
            logger.error(f"Failed to get agent config: {e}")
            return None

    def get_agent_by_name(self, name: str) -> Optional[AgentDo]:
        """Get Agent by name.

        Args:
            name: Agent name

        Returns:
            AgentDo or None

        Example:
            >>> agent_dao = AgentDao(session)
            >>> agent_do = agent_dao.get_agent_by_name("code_expert")
        """
        try:
            results = self.filter_by(name=name)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get agent by name {name}: {e}")
            return None

    def list_experts(self, active_only: bool = True) -> List[AgentDo]:
        """Get all Expert configurations.

        Args:
            active_only: Whether to return only active experts

        Returns:
            List of Expert configurations

        Example:
            >>> agent_dao = AgentDao(session)
            >>> experts = agent_dao.list_experts(active_only=True)
            >>> for expert_do in experts:
            ...     print(f"Expert: {expert_do.name}")
        """
        try:
            filters = {"agent_type": "expert"}
            if active_only:
                filters["is_active"] = True
            return self.filter_by(**filters)
        except Exception as e:
            logger.error(f"Failed to list experts: {e}")
            return []

    def get_leader(self) -> Optional[AgentDo]:
        """Get Leader configuration.

        Assumes there is only one active Leader in the system.

        Returns:
            Leader configuration or None

        Example:
            >>> agent_dao = AgentDao(session)
            >>> leader_do = agent_dao.get_leader()
        """
        try:
            results = self.filter_by(agent_type="leader", is_active=True)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get leader: {e}")
            return None

    # ==================== Update Methods ====================

    def deactivate_agent(self, agent_id: str) -> bool:
        """Deactivate Agent.

        Mark Agent as inactive instead of deleting the record.

        Args:
            agent_id: Agent ID

        Returns:
            Whether successful

        Example:
            >>> agent_dao = AgentDao(session)
            >>> agent_dao.deactivate_agent("agent-123")
        """
        try:
            self.update(agent_id, is_active=False)
            logger.info(f"Deactivated agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate agent {agent_id}: {e}")
            return False

    def activate_agent(self, agent_id: str) -> bool:
        """Activate Agent.

        Args:
            agent_id: Agent ID

        Returns:
            Whether successful

        Example:
            >>> agent_dao = AgentDao(session)
            >>> agent_dao.activate_agent("agent-123")
        """
        try:
            self.update(agent_id, is_active=True)
            logger.info(f"Activated agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to activate agent {agent_id}: {e}")
            return False

    # ==================== Private Helper Methods ====================

    def _extract_reasoner_config(self, reasoner: Reasoner) -> Optional[Dict[str, Any]]:
        """Extract Reasoner configuration.

        Extract serializable configuration parameters from Reasoner instance.

        Args:
            reasoner: Reasoner instance

        Returns:
            Configuration dictionary
        """
        config = {}

        # Extract DualModelReasoner specific attributes
        if hasattr(reasoner, '_actor_name'):
            config['actor_name'] = getattr(reasoner, '_actor_name')
        if hasattr(reasoner, '_thinker_name'):
            config['thinker_name'] = getattr(reasoner, '_thinker_name')

        # Extract common attributes (if exists)
        common_attrs = ['temperature', 'max_tokens', 'top_p', 'model_name']
        for attr in common_attrs:
            if hasattr(reasoner, attr):
                value = getattr(reasoner, attr)
                # Only save basic types
                if isinstance(value, (str, int, float, bool)):
                    config[attr] = value

        return config if config else None

    def _extract_workflow_config(self, workflow: Workflow) -> Optional[Dict[str, Any]]:
        """Extract Workflow configuration.

        Extract serializable configuration parameters from Workflow instance.

        Args:
            workflow: Workflow instance

        Returns:
            Configuration dictionary
        """
        config = {}

        # If workflow has to_config method, use it
        if hasattr(workflow, 'to_config') and callable(workflow.to_config):
            try:
                config = workflow.to_config()
            except Exception as e:
                logger.warning(f"Failed to extract workflow config via to_config: {e}")

        # Extract other common attributes
        if not config:
            common_attrs = ['workflow_type', 'steps', 'operators']
            for attr in common_attrs:
                if hasattr(workflow, attr):
                    value = getattr(workflow, attr)
                    # Only save basic types or serializable types
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        config[attr] = value

        return config if config else None

    def _build_agent_config(self, agent_do: AgentDo) -> AgentConfig:
        """Build AgentConfig from AgentDo.

        Reconstruct AgentConfig object from database record.

        Args:
            agent_do: Database record

        Returns:
            AgentConfig object

        Raises:
            ValueError: If unable to reconstruct configuration
        """
        try:
            # Build Profile
            profile = Profile(
                name=agent_do.name,
                description=agent_do.description or ""
            )

            # Rebuild Reasoner
            reasoner = self._rebuild_reasoner(
                agent_do.reasoner_type,
                agent_do.reasoner_config
            )

            # Rebuild Workflow
            workflow = self._rebuild_workflow(
                agent_do.workflow_type,
                agent_do.workflow_config
            )

            return AgentConfig(
                profile=profile,
                reasoner=reasoner,
                workflow=workflow
            )

        except Exception as e:
            logger.error(f"Failed to build agent config from AgentDo: {e}")
            raise ValueError(f"Cannot rebuild agent config: {e}")

    def _rebuild_reasoner(self, reasoner_type: str, config: Optional[Dict]) -> Reasoner:
        """Rebuild Reasoner from type and configuration.

        Args:
            reasoner_type: Reasoner class name
            config: Configuration parameters

        Returns:
            Reasoner instance

        Raises:
            ValueError: If unable to create Reasoner
        """
        try:
            # Try to use factory method (if exists)
            try:
                from app.core.reasoner.reasoner_factory import ReasonerFactory
                return ReasonerFactory.create(reasoner_type, config or {})
            except ImportError:
                pass

            # Fallback: import and instantiate directly
            if reasoner_type == "DualModelReasoner":
                from app.core.reasoner.dual_model_reasoner import DualModelReasoner
                return DualModelReasoner()
            elif reasoner_type == "MonoModelReasoner":
                from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
                return MonoModelReasoner()
            else:
                logger.warning(f"Unknown reasoner type: {reasoner_type}, using default")
                # Use default Reasoner
                from app.core.reasoner.dual_model_reasoner import DualModelReasoner
                return DualModelReasoner()

        except Exception as e:
            logger.error(f"Failed to rebuild reasoner: {e}")
            raise ValueError(f"Cannot create reasoner {reasoner_type}: {e}")

    def _rebuild_workflow(self, workflow_type: str, config: Optional[Dict]) -> Workflow:
        """Rebuild Workflow from type and configuration.

        Args:
            workflow_type: Workflow class name
            config: Configuration parameters

        Returns:
            Workflow instance

        Raises:
            ValueError: If unable to create Workflow
        """
        try:
            # Try to use factory method (if exists)
            try:
                from app.core.workflow.workflow_factory import WorkflowFactory
                return WorkflowFactory.create(workflow_type, config or {})
            except ImportError:
                pass

            # Fallback: import and instantiate directly
            # Currently only supports BuiltinWorkflow
            if workflow_type == "BuiltinWorkflow":
                from app.core.workflow.workflow import BuiltinWorkflow
                return BuiltinWorkflow()
            else:
                logger.warning(f"Unknown workflow type: {workflow_type}, using default BuiltinWorkflow")
                from app.core.workflow.workflow import BuiltinWorkflow
                return BuiltinWorkflow()

        except Exception as e:
            logger.error(f"Failed to rebuild workflow: {e}")
            raise ValueError(f"Cannot create workflow {workflow_type}: {e}")
