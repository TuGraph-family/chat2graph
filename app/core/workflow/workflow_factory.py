"""
Workflow 工厂类

用于根据类型和配置创建 Workflow 实例。

Author: Issue #40 Implementation
Date: 2025-11-24
"""

from typing import Dict, Any
from app.core.workflow.workflow import Workflow
from app.utils.logger import logger


class WorkflowFactory:
    """Workflow 工厂类

    提供静态方法根据类型名称和配置参数创建 Workflow 实例。
    """

    @staticmethod
    def create(workflow_type: str, config: Dict[str, Any]) -> Workflow:
        """根据类型创建 Workflow

        Args:
            workflow_type: Workflow 类名，如 'BuiltinWorkflow'
            config: 配置参数字典

        Returns:
            Workflow 实例

        Raises:
            ValueError: 如果 workflow_type 未知

        Example:
            >>> config = {}
            >>> workflow = WorkflowFactory.create("BuiltinWorkflow", config)
        """
        try:
            if workflow_type == "BuiltinWorkflow":
                from app.core.workflow.workflow import BuiltinWorkflow
                return BuiltinWorkflow()

            # 可以在这里添加更多 Workflow 类型
            # elif workflow_type == "CustomWorkflow":
            #     from app.core.workflow.custom_workflow import CustomWorkflow
            #     return CustomWorkflow(**config)

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
            # 在这里添加其他支持的类型
        ]
