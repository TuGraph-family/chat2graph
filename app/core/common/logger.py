import logging
from typing import Dict, Tuple
import warnings


class Chat2GraphLoggerMeta(type):
    """Metaclass for centralized logger configuration for the Chat2Graph application."""

    _initialized = False

    def __init__(cls, name: str, bases: Tuple, dct: Dict):
        super().__init__(name, bases, dct)
        if not Chat2GraphLoggerMeta._initialized:
            Chat2GraphLoggerMeta._setup_logging()

    @classmethod
    def _setup_logging(mcs):
        """Setup logging configuration for the entire application."""
        if mcs._initialized:
            return

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # suppress LiteLLM INFO messages
        logging.getLogger("LiteLLM").setLevel(logging.WARNING)
        # suppress httpx INFO messages
        logging.getLogger("httpx").setLevel(logging.WARNING)

        # suppress specific Pydantic UserWarning from LiteLLM, which is noisy as of v1.72.6
        # see: https://github.com/BerriAI/litellm/issues/11759
        warnings.filterwarnings(
            "ignore",
            message="Pydantic serializer warnings.*",
            category=UserWarning,
        )

        mcs._initialized = True

    def get_logger(cls, name: str | None = None):
        """Get a logger instance with proper configuration."""
        return logging.getLogger(name or __name__)


class Chat2GraphLogger(metaclass=Chat2GraphLoggerMeta):
    """Static class to manage centralized logging for the Chat2Graph application.
    
    Usage:
        logger = Chat2GraphLogger.get_logger(__name__)
        logger.info("Your message here")
    """
