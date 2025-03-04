from flask import Blueprint, request

from app.server.common.util import BaseException, make_response
from app.server.manager.graph_db_manager import GraphDBManager

graphdbs_bp = Blueprint("graphdbs", __name__)


@graphdbs_bp.route("/", methods=["GET"])
def get_all_graph_dbs():
    """
    Get all GraphDBs.
    """
    manager = GraphDBManager()
    try:
        graph_dbs, message = manager.get_all_graph_dbs()
        return make_response(True, data=graph_dbs, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/", methods=["POST"])
def create_graph_db():
    """
    Create a new GraphDB.
    """
    manager = GraphDBManager()
    data = request.json
    try:
        required_fields = ["ip", "port", "user", "pwd", "desc", "name", "is_default_db"]
        if not data or not all(field in data for field in required_fields):
            raise BaseException(
                "Missing required fields. Required: ip, port, user, pwd, desc, name, is_default_db"
            )

        new_graph_db, message = manager.create_graph_db(
            ip=data.get("ip"),
            port=data.get("port"),
            user=data.get("user"),
            pwd=data.get("pwd"),
            desc=data.get("desc"),
            name=data.get("name"),
            is_default_db=data.get("is_default_db"),
        )
        return make_response(True, data=new_graph_db, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/<string:graph_db_id>", methods=["GET"])
def get_graph_db_by_id(graph_db_id):
    """
    Get a GraphDB by ID.
    """
    manager = GraphDBManager()
    try:
        graph_db, message = manager.get_graph_db(id=graph_db_id)
        return make_response(True, data=graph_db, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/<string:graph_db_id>", methods=["DELETE"])
def delete_graph_db_by_id(graph_db_id):
    """
    Delete a GraphDB by ID.
    """
    manager = GraphDBManager()
    try:
        result, message = manager.delete_graph_db(id=graph_db_id)
        return make_response(True, data=result, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/<string:graph_db_id>", methods=["PUT"])
def update_graph_db_by_id(graph_db_id):
    """
    Update a GraphDB by ID.
    """
    manager = GraphDBManager()
    data = request.json
    try:
        updated_graph_db, message = manager.update_graph_db(
            id=graph_db_id,
            ip=data.get("ip"),
            port=data.get("port"),
            user=data.get("user"),
            pwd=data.get("pwd"),
            desc=data.get("desc"),
            name=data.get("name"),
            is_default_db=data.get("is_default_db"),
        )
        return make_response(True, data=updated_graph_db, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@graphdbs_bp.route("/validate_connection", methods=["POST"])
def validate_graph_connection():
    """
    Validate connection to a GraphDB.
    """
    manager = GraphDBManager()
    data = request.json
    try:
        required_fields = ["ip", "port", "user", "pwd"]
        if not data or not all(field in data for field in required_fields):
            raise BaseException("Missing required fields. Required: ip, port, user, pwd")

        is_valid, message = manager.validate_graph_connection(
            ip=data.get("ip"), port=data.get("port"), user=data.get("user"), pwd=data.get("pwd")
        )
        return make_response(True, data={"is_valid": is_valid}, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))
