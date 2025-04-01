from typing import Any, Dict, cast

from flask import Blueprint, request

from app.core.model.message import MessageType, TextMessage
from app.core.model.session import Session
from app.server.common.util import ApiException, make_response
from app.server.manager.message_manager import MessageManager
from app.server.manager.session_manager import SessionManager
from app.server.manager.view.message_view import MessageViewTransformer

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/", methods=["GET"])
def get_sessions():
    """Get all sessions."""
    manager = SessionManager()

    size = request.args.get("size", type=int)
    page = request.args.get("page", type=int)

    # Pass these parameters to get_all_sessions
    sessions, message = manager.get_all_sessions(size=size, page=page)
    return make_response(data=sessions, message=message)


@sessions_bp.route("/", methods=["POST"])
def create_session():
    """Create a new session."""
    manager = SessionManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)

    if not data or "name" not in data:
        raise ApiException("Session name is required")
    new_session, message = manager.create_session(name=data.get("name"))
    return make_response(data=new_session, message=message)


@sessions_bp.route("/<string:session_id>", methods=["GET"])
def get_session_by_id(session_id: str):
    """Get a session by ID."""
    manager = SessionManager()

    session, message = manager.get_session(session_id=session_id)
    return make_response(data=session, message=message)


@sessions_bp.route("/<string:session_id>", methods=["DELETE"])
def delete_session_by_id(session_id: str):
    """Delete a session by ID."""
    manager = SessionManager()

    result, message = manager.delete_session(id=session_id)
    return make_response(data=result, message=message)


@sessions_bp.route("/<string:session_id>", methods=["PUT"])
def update_session_by_id(session_id: str):
    """Update a session by ID."""
    manager = SessionManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)

    name = data.get("name")
    assert isinstance(name, str), "Name should be a string"
    session_dict, _ = manager.get_session(session_id=session_id)
    updated_session, message = manager.update_session(
        session=Session(
            id=session_id,
            name=name,
            timestamp=session_dict["timestamp"],
            latest_job_id=session_dict["latest_job_id"],
        )
    )
    return make_response(data=updated_session, message=message)


@sessions_bp.route("/<string:session_id>/job_id", methods=["GET"])
def get_latest_job_id(session_id: str):
    """Get the latest job ID for a session."""
    manager = SessionManager()

    session, message = manager.get_session(session_id=session_id)
    data: Dict[str, Any] = {"id": session["latest_job_id"]}
    return make_response(data=data, message=message)


@sessions_bp.route("/<string:session_id>/chat", methods=["POST"])
def chat(session_id: str):
    """Handle chat message creation."""
    manager = MessageManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)

    if not data:
        raise ApiException("Data is required")

    # add session_id for all messages
    data["instruction_message"]["session_id"] = session_id
    for attached_message in data["attached_messages"]:
        attached_message["session_id"] = session_id

    chat_message: TextMessage = cast(
        TextMessage,
        MessageViewTransformer.deserialize_message(
            message=data, message_type=MessageType.HYBRID_MESSAGE
        ),
    )
    response_data, message = manager.chat(chat_message)
    return make_response(data=response_data, message=message)


@sessions_bp.route("/<string:session_id>/messages", methods=["GET"])
def get_conversion_view(session_id: str):
    """Get message view (including thinking chain) for a specific job.
    Returns the user's question, AI's answer, and thinking chain messages.
    """
    manager = SessionManager()

    message_view_datas, message = manager.get_conversation_views(session_id=session_id)

    return make_response(data=message_view_datas, message=message)
