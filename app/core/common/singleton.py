from abc import ABCMeta
from typing import Any, Dict


class AbcSingleton(ABCMeta):
    """Abstract Singleton metaclass for creating AbcSingleton classes."""

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    @property
    def instance(cls) -> Any:
        """Returns the singleton instance, or None if not yet created."""
        return cls._instances.get(cls, None)


class Singleton(AbcSingleton):
    """Singleton metaclass for creating Singleton classes."""
