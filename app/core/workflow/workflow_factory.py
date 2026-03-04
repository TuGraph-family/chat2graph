"""Workflow Factory.

Creates Workflow instances based on type and configuration.
"""

from typing import Dict, Any, Optional
from app.core.workflow.workflow import Workflow
from app.utils.logger import logger


class WorkflowFactory:
    """Workflow Factory.

    Provides static methods to create Workflow instances based on type name and configuration parameters.
    """

    @staticmethod
    def create(workflow_type: str, config: Optional[Dict[str, Any]] = None) -> Workflow:
        """Create Workflow based on type.

        Args:
            workflow_type: Workflow class name, e.g. 'BuiltinWorkflow'
            config: Configuration parameter dictionary (reserved for extension, currently unused by BuiltinWorkflow)

        Returns:
            Workflow instance

        Raises:
            ValueError: If workflow_type is unknown

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
            # Fallback: return default Workflow
            from app.core.workflow.workflow import BuiltinWorkflow
            return BuiltinWorkflow()

    @staticmethod
    def get_supported_types() -> list:
        """Get list of supported Workflow types.

        Returns:
            List of supported type names
        """
        return [
            "BuiltinWorkflow",
        ]
