from typing import TYPE_CHECKING, Dict, Type, TypeVar, cast

if TYPE_CHECKING:
    pass

T = TypeVar("T")
injection_services_mapping: Dict[Type[T], T] = {}


def setup_injection_services_mapping():
    """Setup the injection services mapping."""
    from app.core.service.graph_db_service import GraphDbService
    from app.core.service.knowledge_base_service import KnowledgeBaseService

    injection_services_mapping[GraphDbService] = cast(GraphDbService, GraphDbService.instance)
    injection_services_mapping[KnowledgeBaseService] = cast(
        KnowledgeBaseService, KnowledgeBaseService.instance
    )
