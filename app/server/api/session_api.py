from typing import Optional

from flask import Blueprint, request

from app.core.common.type import ChatMessageType
from app.server.common.util import ApiException, make_response
from app.server.manager.message_manager import MessageManager
from app.server.manager.session_manager import SessionManager

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/", methods=["GET"])
def get_sessions():
    """Get all sessions."""
    manager = SessionManager()
    try:
        sessions, message = manager.get_all_sessions()
        return make_response(True, data=sessions, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/", methods=["POST"])
def create_session():
    """Create a new session."""
    manager = SessionManager()
    data = request.json
    try:
        if not data or "name" not in data:
            raise ApiException("Session name is required")
        new_session, message = manager.create_session(name=data.get("name"))
        return make_response(True, data=new_session, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["GET"])
def get_session_by_id(session_id):
    """Get a session by ID."""
    manager = SessionManager()
    try:
        session, message = manager.get_session(session_id=session_id)
        return make_response(True, data=session, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["DELETE"])
def delete_session_by_id(session_id):
    """Delete a session by ID."""
    manager = SessionManager()
    try:
        result, message = manager.delete_session(id=session_id)
        return make_response(True, data=result, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["PUT"])
def update_session_by_id(session_id):
    """Update a session by ID."""
    manager = SessionManager()
    data = request.json
    try:
        name = data.get("name")
        assert isinstance(name, Optional[str]), "Name should be a string or None"

        updated_session, message = manager.update_session(id=session_id, name=name)
        return make_response(True, data=updated_session, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>/chat", methods=["POST"])
def chat(session_id):
    """Handle chat message creation."""
    manager = MessageManager()
    data = request.json
    try:
        if not data or "message" not in data:
            raise ApiException("Message is required")

        # Session ID now comes from URL parameter
        assert isinstance(session_id, str), "Session ID should be a string"

        # TODO: rename message to payload
        payload = data.get("message")
        assert isinstance(payload, str), "Message should be a string"

        # TODO: rename message_type to chat_message_type
        chat_message_type = ChatMessageType(data.get("message_type", ChatMessageType.TEXT.value))

        others = data.get("others")
        assert isinstance(others, Optional[str]), "Others should be a string or None"

        file_paths = data.get("file_paths", [])
        assert isinstance(file_paths, list), "File paths should be a list of strings"

        response_data, message = manager.chat(
            session_id=session_id,
            payload=payload,
            chat_message_type=chat_message_type,
            others=others,
        )
        return make_response(True, data=response_data, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
