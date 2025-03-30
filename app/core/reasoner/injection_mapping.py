from typing import TYPE_CHECKING, Dict, cast

if TYPE_CHECKING:
    pass


injection_services_mapping: Dict = {}


def setup_injection_services_mapping():
    """Setup the injection services mapping."""
    from app.core.service.file_service import FileService
    from app.core.service.graph_db_service import GraphDbService
    from app.core.service.knowledge_base_service import KnowledgeBaseService

    injection_services_mapping[GraphDbService] = cast(GraphDbService, GraphDbService.instance)
    injection_services_mapping[KnowledgeBaseService] = cast(
        KnowledgeBaseService, KnowledgeBaseService.instance
    )
    injection_services_mapping[FileService] = cast(FileService, FileService.instance)
