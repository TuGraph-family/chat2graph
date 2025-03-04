from flask import Blueprint, request

from app.server.common.util import BaseException, make_response
from app.server.manager.message_manager import MessageManager

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/chat", methods=["POST"])
def chat():
    """Handle chat message creation."""
    manager = MessageManager()
    data = request.json
    try:
        if not data or "session_id" not in data or "message" not in data:
            raise BaseException("Session ID and message are required")

        session_id = data.get("session_id")
        message = data.get("message")
        message_type = data.get("message_type", "chat")
        others = data.get("others")

        response_data, message = manager.chat(
            session_id=session_id, message=message, message_type=message_type, others=others
        )
        return make_response(True, data=response_data, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@messages_bp.route("/<string:message_id>", methods=["GET"])
def get_message(message_id):
    """Get message details by ID."""
    manager = MessageManager()
    try:
        message_details, message = manager.get_message(id=message_id)
        return make_response(True, data=message_details, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))


@messages_bp.route("/filter", methods=["POST"])
def filter_messages_by_session():
    """Filter messages by session ID."""
    manager = MessageManager()
    data = request.json
    try:
        session_id = data.get("session_id")
        if not session_id:
            raise BaseException("Session ID is required")
        filtered_messages, message = manager.filter_messages_by_session(session_id=session_id)
        return make_response(True, data=filtered_messages, message=message)
    except BaseException as e:
        return make_response(False, message=str(e))
