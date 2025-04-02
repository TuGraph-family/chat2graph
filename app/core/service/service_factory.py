import importlib
import inspect
from pathlib import Path
import pkgutil
from typing import Any, Dict, List, Type

from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService


class ServiceFactory:
    """Automatically discover and initialize all Service classes in app.core.service"""

    # define service initialization order by class name
    # services listed here will be initialized first, in the order specified
    # any services not listed will be initialized after these, in discovery order
    _initialization_order: List[str] = [MessageService.__name__, JobService.__name__]

    @classmethod
    def initialize(cls) -> None:
        """Discover and initialize all Service classes using dynamic import"""
        current_dir = Path(__file__).parent
        service_package_name = __package__

        # first, discover all service classes but don't initialize them yet
        discovered_services: Dict[str, Type[Any]] = {}

        for module_info in pkgutil.iter_modules([str(current_dir)]):
            module_full_name = f"{service_package_name}.{module_info.name}"
            module = importlib.import_module(module_full_name)
            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and obj.__module__ == module_full_name
                    and hasattr(obj, "instance")
                    and obj.__name__.endswith("Service")
                ):
                    discovered_services[obj.__name__] = obj

        # initialize services in specified order first
        for service_name in cls._initialization_order:
            if (
                service_name in discovered_services
                and not discovered_services[service_name].instance
            ):
                discovered_services[service_name]()
                # Remove from dict to avoid initializing twice
                discovered_services.pop(service_name)

        # initialize any remaining services
        for service_class in discovered_services.values():
            if not service_class.instance:
                service_class()
