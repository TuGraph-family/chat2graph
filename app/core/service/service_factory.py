import importlib
import inspect
from pathlib import Path
import pkgutil


class ServiceFactory:
    """Automatically discover and initialize all Service classes in app.core.service"""

    @classmethod
    def initialize(cls) -> None:
        """Discover and initialize all Service classes using dynamic import"""
        current_dir = Path(__file__).parent
        service_package_name = __package__

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
                    if not obj.instance:
                        obj()
