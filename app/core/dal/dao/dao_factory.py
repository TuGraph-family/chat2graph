import importlib
import inspect
from pathlib import Path
import pkgutil

from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao


class DaoFactory:
    """Automatically discover and initialize all DAO classes"""

    @classmethod
    def initialize(cls, session: SqlAlchemySession) -> None:
        """Discover and initialize all DAO classes using dynamic import

        Args:
            session: SQLAlchemy session to be used for all DAOs
        """
        # get package name without the module
        current_dir = Path(__file__).parent
        dao_package_name = ".".join(__name__.split(".")[:-1])

        for module_info in pkgutil.iter_modules([str(current_dir)]):
            module_full_name = f"{dao_package_name}.{module_info.name}"
            module = importlib.import_module(module_full_name)

            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and obj.__module__ == module_full_name
                    and hasattr(obj, "instance")
                    and issubclass(obj, Dao)
                    and obj.__name__ != "Dao"  # skip the base Dao class
                    and obj.__name__.endswith("Dao")
                ):
                    if not obj.instance:
                        # Each concrete DAO implementation (like FileDao) already specifies
                        # its model type in its __init__ method, so we only need to pass session
                        obj(session=session)  # type: ignore
