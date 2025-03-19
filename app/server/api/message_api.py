from typing import Any, Dict

from flask import Blueprint, request

from app.core.model.message import MessageType, TextMessage
from app.server.common.util import ApiException, make_response
from app.server.manager.message_manager import MessageManager
from app.server.manager.view.message_view import MessageView

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/chat", methods=["POST"])
def chat():
    """Handle chat message creation.
    @Warning: This method is deprecated and will be removed to the session API.
    """
    # @Deprecated: This API will be removed
    manager = MessageManager()
    data: Dict[str, Any] = request.json
    try:
        if not data:
            raise ApiException("Data is required")

        # TODO: remove the mocked data
        data["payload"] = (
            "将给定的文本的所有的数据导入到图数据库中（总共至少导入 100 个三元组关系来满足知识图谱的数据丰富性）。"  # noqa: E501
        )

        data["assigned_expert_name"] = "Data Importation Expert"

        text_message: TextMessage = MessageView.deserialize_message(
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
        message_details, message = manager.query_text_message(id=message_id)
        return make_response(True, data=message_details, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
