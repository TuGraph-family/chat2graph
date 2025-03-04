from flask import Blueprint, request

from app.server.common.util import BaseException, make_response
from app.server.manager.session_manager import SessionManager

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/", methods=["GET"])
def get_sessions():
    """Get all sessions."""
    manager = SessionManager()
    try:
        sessions, message = manager.get_all_sessions()
        return make_response(True, data=sessions, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/", methods=["POST"])
def create_session():
    """Create a new session."""
    manager = SessionManager()
    data = request.json
    try:
        if not data or "name" not in data:
            raise BaseException("Session name is required")
        new_session, message = manager.create_session(name=data.get("name"))
        return make_response(True, data=new_session, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["GET"])
def get_session_by_id(session_id):
    """Get a session by ID."""
    manager = SessionManager()
    try:
        session, message = manager.get_session(session_id=session_id)
        return make_response(True, data=session, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["DELETE"])
def delete_session_by_id(session_id):
    """Delete a session by ID."""
    manager = SessionManager()
    try:
        result, message = manager.delete_session(id=session_id)
        return make_response(True, data=result, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["PUT"])
def update_session_by_id(session_id):
    """Update a session by ID."""
    manager = SessionManager()
    data = request.json
    try:
        name = data.get("name")
        updated_session, message = manager.update_session(id=session_id, name=name)
        return make_response(True, data=updated_session, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))
