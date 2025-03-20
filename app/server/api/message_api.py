from typing import Any, Dict

from flask import Blueprint, request

from app.core.model.message import ChatMessage, MessageType
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
        data = {
            "payload": "首先，我需要对给定的文本中的关系进行*复杂*的图建模。这个建模能够覆盖掉文本以及一些文本细节（5 个以上 vertices labels，和同等量级的 edge labels。"
            "然后将给定的文本的所有的数据导入到图数据库中（总共至少导入 100 个三元组关系来满足知识图谱的数据丰富性）。",
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
            # "assigned_expert_name": "Question Answering Expert",
            "assigned_expert_name": None,
        }
        chat_message: ChatMessage = MessageView.deserialize_message(
            message=data, message_type=MessageType.HYBRID_MESSAGE
        )
        response_data, message = manager.chat(chat_message)
        return make_response(True, data=response_data, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
