from typing import Any, Dict, cast

from flask import Blueprint, request

from app.core.common.type import GraphDbType
from app.core.model.graph_db_config import GraphDbConfig
from app.server.common.util import ApiException, make_response
from app.server.manager.graph_db_manager import GraphDBManager

graph_dbs_bp = Blueprint("graphdbs", __name__)


@graph_dbs_bp.route("/", methods=["GET"])
def get_all_graph_dbs():
    """Get all GraphDBs."""
    manager = GraphDBManager()
    graph_dbs, message = manager.get_all_graph_db_configs()
    return make_response(data=graph_dbs, message=message)


@graph_dbs_bp.route("/", methods=["POST"])
def create_graph_db():
    """Create a new GraphDB."""
    manager = GraphDBManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)
    required_fields = ["type", "name", "host", "port"]
    if not data or not all(field in data for field in required_fields):
        raise ApiException(f"Missing required fields: {required_fields}")

    graph_db = GraphDbConfig(
        type=GraphDbType(data.get("type").upper()),
        name=data.get("name"),
        desc=data.get("desc"),
        host=data.get("host"),
        port=int(data.get("port")),
        user=data.get("user"),
        pwd=data.get("pwd"),
        default_schema=data.get("default_schema"),
        is_default_db=data.get("is_default_db"),
    )
    new_graph_db, message = manager.create_graph_db(graph_db_config=graph_db)
    return make_response(data=new_graph_db, message=message)


@graph_dbs_bp.route("/<string:graph_db_id>", methods=["GET"])
def get_graph_db_by_id(graph_db_id: str):
    """Get a GraphDB by ID."""
    manager = GraphDBManager()
    graph_db, message = manager.get_graph_db(id=graph_db_id)
    return make_response(data=graph_db, message=message)


@graph_dbs_bp.route("/<string:graph_db_id>", methods=["DELETE"])
def delete_graph_db_by_id(graph_db_id: str):
    """Delete a GraphDB by ID."""
    manager = GraphDBManager()
    result, message = manager.delete_graph_db(id=graph_db_id)
    return make_response(data=result, message=message)


@graph_dbs_bp.route("/<string:graph_db_id>", methods=["PUT"])
def update_graph_db_by_id(graph_db_id: str):
    """Update a GraphDB by ID."""
    manager = GraphDBManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)

    graph_db = GraphDbConfig(
        id=graph_db_id,
        type=GraphDbType(data.get("type", GraphDbType.NEO4J.value)),
        name=data["name"],
        desc=data["desc"],
        host=data["host"],
        port=data["port"],
        user=data["user"],
        pwd=data["pwd"],
        is_default_db=data["is_default_db"],
        default_schema=data["default_schema"],
    )
    result, message = manager.update_graph_db(graph_db_config=graph_db)
    return make_response(data=result, message=message)


@graph_dbs_bp.route("/validate_connection", methods=["POST"])
def validate_graph_connection():
    """Validate connection to a GraphDB."""
    manager = GraphDBManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)
    required_fields = ["host", "port", "user", "pwd"]
    if not data or not all(field in data for field in required_fields):
        raise ApiException(f"Missing required fields: {required_fields}")

    graph_db_config = GraphDbConfig(
        type=GraphDbType(data.get("type").upper()),
        name="",
        host=data.get("host"),
        port=data.get("port"),
        user=data.get("user"),
        pwd=data.get("pwd"),
    )
    is_valid, message = manager.validate_graph_db_connection(graph_db_config=graph_db_config)
    return make_response(data={"is_valid": is_valid}, message=message)
