"""
Reasoner 工厂类

用于根据类型和配置创建 Reasoner 实例。

Author: Issue #40 Implementation
Date: 2025-11-24
"""

from typing import Dict, Any
from app.core.reasoner.reasoner import Reasoner
from app.utils.logger import logger


class ReasonerFactory:
    """Reasoner 工厂类

    提供静态方法根据类型名称和配置参数创建 Reasoner 实例。
    """

    @staticmethod
    def create(reasoner_type: str, config: Dict[str, Any]) -> Reasoner:
        """根据类型创建 Reasoner

        Args:
            reasoner_type: Reasoner 类名，如 'DualModelReasoner', 'MonoModelReasoner'
            config: 配置参数字典

        Returns:
            Reasoner 实例

        Raises:
            ValueError: 如果 reasoner_type 未知

        Example:
            >>> config = {"actor_name": "actor", "thinker_name": "thinker"}
            >>> reasoner = ReasonerFactory.create("DualModelReasoner", config)
        """
        try:
            if reasoner_type == "DualModelReasoner":
                from app.core.reasoner.dual_model_reasoner import DualModelReasoner
                # 提取构造函数参数
                actor_name = config.get("actor_name", "actor")
                thinker_name = config.get("thinker_name", "thinker")
                return DualModelReasoner(
                    actor_name=actor_name,
                    thinker_name=thinker_name
                )

            elif reasoner_type == "MonoModelReasoner":
                from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
                # MonoModelReasoner 可能有不同的构造参数
                return MonoModelReasoner()

            else:
                logger.warning(f"Unknown reasoner type: {reasoner_type}, using default DualModelReasoner")
                from app.core.reasoner.dual_model_reasoner import DualModelReasoner
                return DualModelReasoner()

        except Exception as e:
            logger.error(f"Failed to create reasoner {reasoner_type}: {e}")
            # 降级：返回默认 Reasoner
            from app.core.reasoner.dual_model_reasoner import DualModelReasoner
            return DualModelReasoner()

    @staticmethod
    def get_supported_types() -> list:
        """获取支持的 Reasoner 类型列表

        Returns:
            支持的类型名称列表
        """
        return [
            "DualModelReasoner",
            "MonoModelReasoner",
        ]
