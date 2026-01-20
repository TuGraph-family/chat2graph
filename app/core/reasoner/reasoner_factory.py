"""Reasoner Factory.

Creates Reasoner instances based on type and configuration.
"""

from typing import Dict, Any, Optional
from app.core.reasoner.reasoner import Reasoner
from app.utils.logger import logger


class ReasonerFactory:
    """Reasoner Factory.

    Provides static methods to create Reasoner instances based on type name and configuration parameters.
    """

    @staticmethod
    def create(reasoner_type: str, config: Optional[Dict[str, Any]] = None) -> Reasoner:
        """Create Reasoner based on type.

        Args:
            reasoner_type: Reasoner class name, e.g. 'DualModelReasoner', 'MonoModelReasoner'
            config: Configuration parameter dictionary

        Returns:
            Reasoner instance

        Raises:
            ValueError: If reasoner_type is unknown

        Example:
            >>> config = {"actor_name": "actor", "thinker_name": "thinker"}
            >>> reasoner = ReasonerFactory.create("DualModelReasoner", config)
        """
        config = config or {}

        try:
            if reasoner_type == "DualModelReasoner":
                from app.core.reasoner.dual_model_reasoner import DualModelReasoner
                # Extract constructor parameters
                actor_name = config.get("actor_name", "actor")
                thinker_name = config.get("thinker_name", "thinker")
                return DualModelReasoner(
                    actor_name=actor_name,
                    thinker_name=thinker_name
                )

            elif reasoner_type == "MonoModelReasoner":
                from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
                return MonoModelReasoner()

            else:
                logger.warning(f"Unknown reasoner type: {reasoner_type}, using default DualModelReasoner")
                from app.core.reasoner.dual_model_reasoner import DualModelReasoner
                # Use config if available for fallback
                actor_name = config.get("actor_name", "actor")
                thinker_name = config.get("thinker_name", "thinker")
                return DualModelReasoner(
                    actor_name=actor_name,
                    thinker_name=thinker_name
                )

        except Exception as e:
            logger.error(f"Failed to create reasoner {reasoner_type}: {e}")
            # Fallback: return default Reasoner, still try to use config
            from app.core.reasoner.dual_model_reasoner import DualModelReasoner
            try:
                actor_name = config.get("actor_name", "actor")
                thinker_name = config.get("thinker_name", "thinker")
                return DualModelReasoner(
                    actor_name=actor_name,
                    thinker_name=thinker_name
                )
            except Exception:
                # Final fallback: use completely default values
                return DualModelReasoner()

    @staticmethod
    def get_supported_types() -> list:
        """Get list of supported Reasoner types.

        Returns:
            List of supported type names
        """
        return [
            "DualModelReasoner",
            "MonoModelReasoner",
        ]
