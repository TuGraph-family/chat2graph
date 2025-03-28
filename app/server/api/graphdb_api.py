from typing import Any, Dict, cast

from flask import Blueprint, request

from app.core.model.graph_db import GraphDbConfig
from app.server.common.util import ApiException, make_response
from app.server.manager.graph_db_manager import GraphDBManager

graphdbs_bp = Blueprint("graphdbs", __name__)


@graphdbs_bp.route("/", methods=["GET"])
def get_all_graph_dbs():
    """Get all GraphDBs."""
    manager = GraphDBManager()
    try:
        graph_dbs, message = manager.get_all_graph_db_configs()
        return make_response(True, data=graph_dbs, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/", methods=["POST"])
def create_graph_db():
    """Create a new GraphDB."""
    manager = GraphDBManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)
    try:
        required_fields = ["ip", "port", "user", "pwd", "desc", "name", "is_default_db"]
        if not data or not all(field in data for field in required_fields):
            raise ApiException(
                "Missing required fields. Required: ip, port, user, pwd, desc, name, is_default_db"
            )

        graph_db_config = GraphDbConfig(
            ip=data.get("ip"),
            port=data.get("port"),
            user=data.get("user"),
            pwd=data.get("pwd"),
            desc=data.get("desc"),
            name=data.get("name"),
            is_default_db=data.get("is_default_db"),
        )
        new_graph_db, message = manager.create_graph_db(graph_db_config=graph_db_config)
        return make_response(True, data=new_graph_db, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/<string:graph_db_id>", methods=["GET"])
def get_graph_db_by_id(graph_db_id: str):
    """Get a GraphDB by ID."""
    manager = GraphDBManager()
    try:
        graph_db, message = manager.get_graph_db(id=graph_db_id)
        return make_response(True, data=graph_db, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/<string:graph_db_id>", methods=["DELETE"])
def delete_graph_db_by_id(graph_db_id: str):
    """Delete a GraphDB by ID."""
    manager = GraphDBManager()
    try:
        result, message = manager.delete_graph_db(id=graph_db_id)
        return make_response(True, data=result, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/<string:graph_db_id>", methods=["PUT"])
def update_graph_db_by_id(graph_db_id: str):
    """Update a GraphDB by ID."""
    manager = GraphDBManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)
    try:
        required_fields = ["ip", "port", "user", "pwd", "desc", "name", "is_default_db"]
        if not data or not all(field in data for field in required_fields):
            raise ApiException(
                "Missing required fields. Required: ip, port, user, pwd, desc, name, is_default_db"
            )
        graph_db_config = GraphDbConfig(
            id=graph_db_id,
            ip=data["ip"],
            port=data["port"],
            user=data["user"],
            pwd=data["pwd"],
            desc=data["desc"],
            name=data["name"],
            is_default_db=data["is_default_db"],
        )
        updated_graph_db, message = manager.update_graph_db(graph_db_config=graph_db_config)
        return make_response(True, data=updated_graph_db, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/validate_connection", methods=["POST"])
def validate_graph_connection():
    """Validate connection to a GraphDB."""
    manager = GraphDBManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)
    try:
        required_fields = ["ip", "port", "user", "pwd"]
        if not data or not all(field in data for field in required_fields):
            raise ApiException("Missing required fields. Required: ip, port, user, pwd")

        graph_db_config = GraphDbConfig(
            ip=data.get("ip"),
            port=data.get("port"),
            user=data.get("user"),
            pwd=data.get("pwd"),
            desc="",
            name="",
            is_default_db=False,
        )
        is_valid, message = manager.validate_graph_db_connection(graph_db_config=graph_db_config)
        return make_response(True, data={"is_valid": is_valid}, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
