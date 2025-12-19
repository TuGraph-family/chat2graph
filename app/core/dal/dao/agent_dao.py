"""
Agent 数据访问对象

提供 Agent 配置的 CRUD 操作和配置重建功能。

Author: kaichuan
Date: 2025-11-24
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
    """Agent 数据访问对象

    提供 Agent 配置的持久化、查询和重建功能。

    Attributes:
        model_class: AgentDo 数据模型类
        session: SQLAlchemy 会话
    """

    def __init__(self, session: Session):
        """初始化 AgentDao

        Args:
            session: SQLAlchemy 会话
        """
        super().__init__(AgentDo, session)

    # ==================== 保存方法 ====================

    def save_agent_config(self, agent: Agent) -> AgentDo:
        """保存 Agent 配置到数据库

        从 Agent 实例提取配置信息并持久化。
        如果 agent 已存在（根据 ID），则更新；否则创建新记录。

        Args:
            agent: Agent 实例

        Returns:
            AgentDo: 保存的数据对象

        Example:
            >>> from app.core.agent.expert import Expert
            >>> agent_dao = AgentDao(session)
            >>> expert = Expert(agent_config)
            >>> agent_do = agent_dao.save_agent_config(expert)
        """
        try:
            # 检查是否已存在
            existing = self.get_by_id(agent._id)

            # 提取配置
            config_data = self._extract_agent_config(agent)

            if existing:
                # 更新现有记录
                logger.info(f"Updating existing agent config: {agent._id}")
                self.update(agent._id, **config_data)
                return self.get_by_id(agent._id)
            else:
                # 创建新记录
                logger.info(f"Creating new agent config: {agent._id}")
                config_data["id"] = agent._id
                return self.create(**config_data)

        except Exception as e:
            logger.error(f"Failed to save agent config: {e}")
            raise

    def _extract_agent_config(self, agent: Agent) -> Dict[str, Any]:
        """从 Agent 实例提取配置信息

        Args:
            agent: Agent 实例

        Returns:
            配置字典
        """
        # 确定 agent 类型
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

        # Leader 特定配置
        if agent_type == "leader" and hasattr(agent, '_leader_state'):
            config_data["leader_state_type"] = agent._leader_state.__class__.__name__

        return config_data

    # ==================== 查询方法 ====================

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取 Agent 配置并重建 AgentConfig

        从数据库读取配置并构建 AgentConfig 对象，用于重建 Agent 实例。

        Args:
            agent_id: Agent ID

        Returns:
            AgentConfig 或 None（如果不存在）

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
        """根据名称获取 Agent

        Args:
            name: Agent 名称

        Returns:
            AgentDo 或 None

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
        """获取所有 Expert 配置

        Args:
            active_only: 是否只返回激活的 experts

        Returns:
            Expert 配置列表

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
        """获取 Leader 配置

        假设系统中只有一个激活的 Leader。

        Returns:
            Leader 配置或 None

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

    # ==================== 更新方法 ====================

    def deactivate_agent(self, agent_id: str) -> bool:
        """停用 Agent

        将 Agent 标记为非激活状态，而不删除记录。

        Args:
            agent_id: Agent ID

        Returns:
            是否成功

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
        """激活 Agent

        Args:
            agent_id: Agent ID

        Returns:
            是否成功

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

    # ==================== 私有辅助方法 ====================

    def _extract_reasoner_config(self, reasoner: Reasoner) -> Optional[Dict[str, Any]]:
        """提取 Reasoner 配置

        从 Reasoner 实例中提取可序列化的配置参数。

        Args:
            reasoner: Reasoner 实例

        Returns:
            配置字典
        """
        config = {}

        # 提取 DualModelReasoner 特定属性
        if hasattr(reasoner, '_actor_name'):
            config['actor_name'] = getattr(reasoner, '_actor_name')
        if hasattr(reasoner, '_thinker_name'):
            config['thinker_name'] = getattr(reasoner, '_thinker_name')

        # 提取通用属性（如果存在）
        common_attrs = ['temperature', 'max_tokens', 'top_p', 'model_name']
        for attr in common_attrs:
            if hasattr(reasoner, attr):
                value = getattr(reasoner, attr)
                # 只保存基本类型
                if isinstance(value, (str, int, float, bool)):
                    config[attr] = value

        return config if config else None

    def _extract_workflow_config(self, workflow: Workflow) -> Optional[Dict[str, Any]]:
        """提取 Workflow 配置

        从 Workflow 实例中提取可序列化的配置参数。

        Args:
            workflow: Workflow 实例

        Returns:
            配置字典
        """
        config = {}

        # 如果 workflow 有 to_config 方法，使用它
        if hasattr(workflow, 'to_config') and callable(workflow.to_config):
            try:
                config = workflow.to_config()
            except Exception as e:
                logger.warning(f"Failed to extract workflow config via to_config: {e}")

        # 提取其他通用属性
        if not config:
            common_attrs = ['workflow_type', 'steps', 'operators']
            for attr in common_attrs:
                if hasattr(workflow, attr):
                    value = getattr(workflow, attr)
                    # 只保存基本类型或可序列化类型
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        config[attr] = value

        return config if config else None

    def _build_agent_config(self, agent_do: AgentDo) -> AgentConfig:
        """从 AgentDo 构建 AgentConfig

        根据数据库记录重建 AgentConfig 对象。

        Args:
            agent_do: 数据库记录

        Returns:
            AgentConfig 对象

        Raises:
            ValueError: 如果无法重建配置
        """
        try:
            # 构建 Profile
            profile = Profile(
                name=agent_do.name,
                description=agent_do.description or ""
            )

            # 重建 Reasoner
            reasoner = self._rebuild_reasoner(
                agent_do.reasoner_type,
                agent_do.reasoner_config
            )

            # 重建 Workflow
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
        """根据类型和配置重建 Reasoner

        Args:
            reasoner_type: Reasoner 类名
            config: 配置参数

        Returns:
            Reasoner 实例

        Raises:
            ValueError: 如果无法创建 Reasoner
        """
        try:
            # 尝试使用工厂方法（如果存在）
            try:
                from app.core.reasoner.reasoner_factory import ReasonerFactory
                return ReasonerFactory.create(reasoner_type, config or {})
            except ImportError:
                pass

            # 降级方案：直接导入并实例化
            # 这里需要根据实际的 Reasoner 实现来调整
            if reasoner_type == "DualModelReasoner":
                from app.core.reasoner.dual_model_reasoner import DualModelReasoner
                return DualModelReasoner()
            elif reasoner_type == "MonoModelReasoner":
                from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
                return MonoModelReasoner()
            else:
                logger.warning(f"Unknown reasoner type: {reasoner_type}, using default")
                # 使用默认 Reasoner
                from app.core.reasoner.dual_model_reasoner import DualModelReasoner
                return DualModelReasoner()

        except Exception as e:
            logger.error(f"Failed to rebuild reasoner: {e}")
            raise ValueError(f"Cannot create reasoner {reasoner_type}: {e}")

    def _rebuild_workflow(self, workflow_type: str, config: Optional[Dict]) -> Workflow:
        """根据类型和配置重建 Workflow

        Args:
            workflow_type: Workflow 类名
            config: 配置参数

        Returns:
            Workflow 实例

        Raises:
            ValueError: 如果无法创建 Workflow
        """
        try:
            # 尝试使用工厂方法（如果存在）
            try:
                from app.core.workflow.workflow_factory import WorkflowFactory
                return WorkflowFactory.create(workflow_type, config or {})
            except ImportError:
                pass

            # 降级方案：直接导入并实例化
            # 当前仅支持 BuiltinWorkflow
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
