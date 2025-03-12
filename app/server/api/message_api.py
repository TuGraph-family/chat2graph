from flask import Blueprint, request

from app.core.model.message import MessageType, TextMessage
from app.server.common.util import ApiException, make_response
from app.server.manager.message_manager import MessageManager
from app.server.manager.view.session_view import SessionView

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/chat", methods=["POST"])
def chat():
    """Handle chat message creation.
    @Warning: This method is deprecated and will be removed to the session API.
    """
    # @Deprecated: This API will be removed
    manager = MessageManager()
    data = request.json
    try:
        if not data:
            raise ApiException("Data is required")

        text_message: TextMessage = SessionView.deserialize_message(
            message=data, message_type=MessageType.TEXT_MESSAGE
        )
        response_data, message = manager.chat(text_message)
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
