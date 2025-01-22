from abc import ABCMeta
from typing import Any, Dict


class AbcSingleton(ABCMeta):
    """Abstract Singleton metaclass for creating AbcSingleton classes."""

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(type):
    """Singleton metaclass for creating Singleton classes."""

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
