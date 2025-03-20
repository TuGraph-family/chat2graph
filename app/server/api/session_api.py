from typing import Any, Dict, List, Optional

from flask import Blueprint, request

from app.core.model.message import MessageType, TextMessage
from app.core.model.session import Session
from app.server.common.util import ApiException, make_response
from app.server.manager.job_manager import JobManager
from app.server.manager.message_manager import MessageManager
from app.server.manager.session_manager import SessionManager
from app.server.manager.view.message_view import MessageViewTransformer

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/", methods=["GET"])
def get_sessions():
    """Get all sessions."""
    manager = SessionManager()
    try:
        size = request.args.get("size", type=int)
        page = request.args.get("page", type=int)

        # Pass these parameters to get_all_sessions
        sessions, message = manager.get_all_sessions(size=size, page=page)
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
        timestamp = data.get("timestamp")
        latest_job_id = data.get("latest_job_id")
        assert isinstance(name, Optional[str]), "Name should be a string or None"
        assert isinstance(timestamp, Optional[int]), "Timestamp should be an integer or None"
        assert isinstance(latest_job_id, Optional[str]), "Latest job ID should be a string or None"

        updated_session, message = manager.update_session(
            session=Session(
                id=session_id, name=name, timestamp=timestamp, latest_job_id=latest_job_id
            )
        )
        return make_response(True, data=updated_session, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>/job_id", methods=["GET"])
def get_latest_job_id(session_id):
    """Get the latest job ID for a session."""
    manager = SessionManager()
    try:
        session, message = manager.get_session(session_id=session_id)
        data = {"id": session["latest_job_id"]}
        return make_response(True, data=data, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>/chat", methods=["POST"])
def chat(session_id):
    """Handle chat message creation."""
    manager = MessageManager()
    data = request.json
    try:
        if not data:
            raise ApiException("Data is required")

        # add session_id for all messages
        data["instruction_message"]["session_id"] = session_id
        for attached_message in data["attached_messages"]:
            attached_message["session_id"] = session_id

        # TODO: remove the mocked data
        data["instruction_message"]["assigned_expert_name"] = "Question Answering Expert"

        chat_message: TextMessage = MessageViewTransformer.deserialize_message(
            message=data, message_type=MessageType.HYBRID_MESSAGE
        )
        response_data, message = manager.chat(chat_message)
        return make_response(True, data=response_data, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>/messages", methods=["GET"])
def get_conversion_view(session_id):
    """Get message view (including thinking chain) for a specific job.
    Returns the user's question, AI's answer, and thinking chain messages.
    """
    job_manager = JobManager()
    session_manager = SessionManager()

    try:
        message_view_datas: List[Dict[str, Any]] = []

        # get all sessions
        job_ids, _ = session_manager.get_all_job_ids(session_id=session_id)

        # get message view data for the job
        for job_id in job_ids:
            message_view_data, _ = job_manager.get_conversation_view(job_id=job_id)
            message_view_datas.append(message_view_data)

        return make_response(
            True, data=message_view_datas, message="Get message views successfully"
        )
    except ApiException as e:
        return make_response(False, message=str(e))
