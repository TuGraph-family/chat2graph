import json
from typing import Any, Dict, cast

from flask import Blueprint, request

from app.server.common.util import ApiException, make_response
from app.server.manager.knowledge_base_manager import KnowledgeBaseManager
from app.server.manager.view.knowledge_base_view import KnowledgeBaseViewTransformer

knowledgebases_bp = Blueprint("knowledgebases", __name__)


@knowledgebases_bp.route("/", methods=["GET"])
def get_all_knowledge_bases():
    """Get all knowledge bases."""
    manager = KnowledgeBaseManager()

    knowledge_bases, message = manager.get_all_knowledge_bases()
    return make_response(data=knowledge_bases, message=message)


@knowledgebases_bp.route("/<string:knowledge_base_id>", methods=["GET"])
def get_knowledge_base_by_id(knowledge_base_id: str):
    """Get a knowledge base by ID."""
    manager = KnowledgeBaseManager()

    knowledge_base, message = manager.get_knowledge_base(id=knowledge_base_id)
    return make_response(data=knowledge_base, message=message)


@knowledgebases_bp.route("/<string:knowledge_base_id>", methods=["PUT"])
def update_knowledge_base_by_id(knowledge_base_id: str):
    """Update a knowledge base by ID."""
    manager = KnowledgeBaseManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)

    required_fields = ["name", "description"]
    if not data or not all(field in data for field in required_fields):
        raise ApiException("Missing required fields. Required: name, description")

    result, message = manager.update_knowledge_base(
        id=knowledge_base_id, name=data["name"], description=data["description"]
    )
    return make_response(data=result, message=message)


@knowledgebases_bp.route("/<string:knowledge_base_id>", methods=["DELETE"])
def delete_knowledge_base_by_id(knowledge_base_id: str):
    """Delete a knowledge base by ID."""
    manager = KnowledgeBaseManager()

    result, message = manager.delete_knowledge_base(id=knowledge_base_id)
    return make_response(data=result, message=message)


@knowledgebases_bp.route("/<string:knowledge_base_id>/files/<string:file_id>", methods=["POST"])
def load_knowledge_with_file_id(knowledge_base_id: str, file_id: str):
    """Load knowledge with file ID."""
    manager = KnowledgeBaseManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)

    required_fields = ["config"]
    if not data or not all(field in data for field in required_fields):
        raise ApiException("Missing required fields. Required: config")
    result, message = manager.load_knowledge(
        kb_id=knowledge_base_id,
        file_id=file_id,
        knowledge_config=KnowledgeBaseViewTransformer.deserialize_knowledge_config(
            json.loads(data.get("config", "{}"))
        ),
    )
    return make_response(data=result, message=message)


@knowledgebases_bp.route("/<string:knowledge_base_id>/files/<string:file_id>", methods=["DELETE"])
def delete_knowledge_with_file_id(knowledge_base_id: str, file_id: str):
    """Load knowledge with file ID."""
    manager = KnowledgeBaseManager()

    result, message = manager.delete_knowledge(kb_id=knowledge_base_id, file_id=file_id)
    return make_response(data=result, message=message)
