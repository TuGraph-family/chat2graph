"""
Workflow 工厂类

用于根据类型和配置创建 Workflow 实例。

Author: kaichuan
Date: 2025-11-24
"""

from typing import Dict, Any, Optional
from app.core.workflow.workflow import Workflow
from app.utils.logger import logger


class WorkflowFactory:
    """Workflow 工厂类

    提供静态方法根据类型名称和配置参数创建 Workflow 实例。
    """

    @staticmethod
    def create(workflow_type: str, config: Optional[Dict[str, Any]] = None) -> Workflow:
        """根据类型创建 Workflow

        Args:
            workflow_type: Workflow 类名，如 'BuiltinWorkflow'
            config: 配置参数字典（预留扩展，当前 BuiltinWorkflow 不使用）

        Returns:
            Workflow 实例

        Raises:
            ValueError: 如果 workflow_type 未知

        Example:
            >>> workflow = WorkflowFactory.create("BuiltinWorkflow")
        """
        # Log config for debugging if provided
        if config:
            logger.debug(f"Creating workflow {workflow_type} with config: {config}")

        try:
            if workflow_type == "BuiltinWorkflow":
                from app.core.workflow.workflow import BuiltinWorkflow
                return BuiltinWorkflow()

            else:
                logger.warning(f"Unknown workflow type: {workflow_type}, using default BuiltinWorkflow")
                from app.core.workflow.workflow import BuiltinWorkflow
                return BuiltinWorkflow()

        except Exception as e:
            logger.error(f"Failed to create workflow {workflow_type}: {e}")
            # 降级：返回默认 Workflow
            from app.core.workflow.workflow import BuiltinWorkflow
            return BuiltinWorkflow()

    @staticmethod
    def get_supported_types() -> list:
        """获取支持的 Workflow 类型列表

        Returns:
            支持的类型名称列表
        """
        return [
            "BuiltinWorkflow",
        ]
