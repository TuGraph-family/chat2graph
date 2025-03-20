from flask import Blueprint, request

from app.core.model.message import ChatMessage, MessageType
from app.server.common.util import ApiException, make_response
from app.server.manager.message_manager import MessageManager
from app.server.manager.view.message_view import MessageViewTransformer

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
        # TODO: remove the mocked data
        data = {
            "payload": "请写一个图数据库 Cypher 语句",
            "message_type": "TEXT",
            "session_id": None,
            "attached_messages": [
                {
                    "file_id": "f7d42c39-e821-47c5-9d36-5f42a8e10db2",
                    "message_type": "FILE",
                    "session_id": None,
                },
                {
                    "file_id": "a8c31f20-d952-4e76-8c15-3e9bf42d8a7c",
                    "message_type": "FILE",
                    "session_id": None,
                },
            ],
            "assigned_expert_name": "Question Answering Expert",
        }
        chat_message: ChatMessage = MessageViewTransformer.deserialize_message(
            message=data, message_type=MessageType.HYBRID_MESSAGE
        )
        response_data, message = manager.chat(chat_message)
        return make_response(True, data=response_data, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
