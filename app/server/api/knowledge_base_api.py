from flask import Blueprint, request

from app.server.common.util import ApiException, make_response
from app.server.manager.knowledge_base_manager import KnowledgeBaseManager

knowledgebases_bp = Blueprint("knowledgebases", __name__)


@knowledgebases_bp.route("/", methods=["GET"])
def get_all_knowledge_bases():
    """Get all knowledge bases."""
    manager = KnowledgeBaseManager()
    try:
        knowledge_bases, message = manager.get_all_knowledge_bases()
        return make_response(True, data=knowledge_bases, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@knowledgebases_bp.route("/", methods=["POST"])
def create_knowledge_base():
    """Create a new knowledge base."""
    manager = KnowledgeBaseManager()
    data = request.json
    try:
        required_fields = ["name", "knowledge_type", "session_id"]
        if not data or not all(field in data for field in required_fields):
            raise ApiException(
                "Missing required fields. Required: name, knowledge_type, session_id"
            )

        new_knowledge_base, message = manager.create_knowledge_base(
            name=data.get("name"),
            knowledge_type=data.get("knowledge_type"),
            session_id=data.get("session_id"),
        )
        return make_response(True, data=new_knowledge_base, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@knowledgebases_bp.route("/<string:knowledge_base_id>", methods=["GET"])
def get_knowledge_base_by_id(knowledge_base_id):
    """Get a knowledge base by ID."""
    manager = KnowledgeBaseManager()
    try:
        knowledge_base, message = manager.get_knowledge_base(id=knowledge_base_id)
        return make_response(True, data=knowledge_base, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@knowledgebases_bp.route("/<string:knowledge_base_id>", methods=["DELETE"])
def delete_knowledge_base_by_id(knowledge_base_id):
    """Delete a knowledge base by ID."""
    manager = KnowledgeBaseManager()
    try:
        result, message = manager.delete_knowledge_base(id=knowledge_base_id)
        return make_response(True, data=result, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
