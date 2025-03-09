from typing import Optional

from flask import Blueprint, request

from app.server.common.util import ApiException, make_response
from app.server.manager.message_manager import MessageManager

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/chat", methods=["POST"])
def chat():
    """Handle chat message creation."""
    manager = MessageManager()
    data = request.json
    try:
        if not data or "session_id" not in data or "message" not in data:
            raise ApiException("Session ID and message are required")

        session_id = data.get("session_id")
        assert isinstance(session_id, str), "Session ID should be a string"

        # TODO: rename message to payload
        payload = data.get("message")
        assert isinstance(payload, str), "Message should be a string"

        # TODO: rename message_type to chat_message_type, and replace the default value with enum
        chat_message_type = data.get("message_type", "chat")
        assert isinstance(chat_message_type, str), "Message type should be a string"

        others = data.get("others")
        assert others is None or isinstance(others, Optional[str]), (
            "Others should be a string or None"
        )

        response_data, message = manager.chat(
            session_id=session_id,
            payload=payload,
            chat_message_type=chat_message_type,
            others=others,
        )
        return make_response(True, data=response_data, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@messages_bp.route("/<string:message_id>", methods=["GET"])
def get_text_message(message_id):
    """Get message details by ID."""
    manager = MessageManager()
    try:
        message_details, message = manager.get_text_message(id=message_id)
        return make_response(True, data=message_details, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@messages_bp.route("/filter", methods=["POST"])
def filter_messages_by_session():
    """Filter messages by session ID."""
    manager = MessageManager()
    data = request.json
    try:
        session_id = data.get("session_id")
        assert isinstance(session_id, str), "Session ID should be a string"

        filtered_messages, message = manager.filter_text_messages_by_session(session_id=session_id)
        return make_response(True, data=filtered_messages, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@messages_bp.route("/job/<string:original_job_id>", methods=["GET"])
def get_agent_messages_by_job_id(original_job_id):
    """Get agent messages by job ID."""
    manager = MessageManager()
    try:
        messages, message = manager.get_agent_messages_by_job(original_job_id=original_job_id)
        return make_response(True, data=messages, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
