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
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)
    try:
        if not data or "name" not in data:
            raise ApiException("Session name is required")
        new_session, message = manager.create_session(name=data.get("name"))
        return make_response(True, data=new_session, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["GET"])
def get_session_by_id(session_id: str):
    """Get a session by ID."""
    manager = SessionManager()
    try:
        session, message = manager.get_session(session_id=session_id)
        return make_response(True, data=session, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["DELETE"])
def delete_session_by_id(session_id: str):
    """Delete a session by ID."""
    manager = SessionManager()
    try:
        result, message = manager.delete_session(id=session_id)
        return make_response(True, data=result, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>", methods=["PUT"])
def update_session_by_id(session_id: str):
    """Update a session by ID."""
    manager = SessionManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)
    try:
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
        return make_response(True, data=updated_session, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>/job_id", methods=["GET"])
def get_latest_job_id(session_id: str):
    """Get the latest job ID for a session."""
    manager = SessionManager()
    try:
        session, message = manager.get_session(session_id=session_id)
        data: Dict[str, Any] = {"id": session["latest_job_id"]}
        return make_response(True, data=data, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>/chat", methods=["POST"])
def chat(session_id: str):
    """Handle chat message creation."""
    manager = MessageManager()
    data: Dict[str, Any] = cast(Dict[str, Any], request.json)
    try:
        if not data:
            raise ApiException("Data is required")

        # add session_id for all messages
        data["instruction_message"]["session_id"] = session_id
        for attached_message in data["attached_messages"]:
            attached_message["session_id"] = session_id

        # TODO: remove the mocked data
        # data["instruction_message"]["payload"] = (
        #     # # "首先，我需要对给定的文本中的关系进行*复杂*的图建模。这个建模能够覆盖掉文本以及一些文本细节（5 个以上 vertices labels，和同等量级的 edge labels。"  # noqa: E501
        #     # # "然后将给定的文本的所有的数据导入到图数据库中（总共至少导入 30 个三元组关系来满足知识图谱的数据丰富性）。"  # noqa: E501
        #     # # "朱丽叶节点有哪些属性。需要拆分成 3 个子任务。"
        #     # "莎士比亚的悲剧《罗密欧与朱丽叶》描述了两个敌对家族（蒙太古家族和凯普莱特家族）中的年轻人之间的爱情故事。"
        #     # "假设我们已经将《罗密欧与朱丽叶》的三元组图谱数据导入到图数据库中。"
        #     # "现在，通过图数据库建模和算法分析，我们可以从网络科学的角度重新审视这部经典作品中的人物关系结构。"
        #     # # "因此，请你使用PageRank算法分析剧中最具影响力的人物。"
        #     "AWEL是什么？"
        # )
        # data["instruction_message"]["assigned_expert_name"] = "Graph Analysis Expert"
        data["instruction_message"]["assigned_expert_name"] = "Question Answering Expert"
        # data["instruction_message"]["assigned_expert_name"] = "Graph Query Expert"

        chat_message: TextMessage = cast(
            TextMessage,
            MessageViewTransformer.deserialize_message(
                message=data, message_type=MessageType.HYBRID_MESSAGE
            ),
        )
        response_data, message = manager.chat(chat_message)
        return make_response(True, data=response_data, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@sessions_bp.route("/<string:session_id>/messages", methods=["GET"])
def get_conversion_view(session_id: str):
    """Get message view (including thinking chain) for a specific job.
    Returns the user's question, AI's answer, and thinking chain messages.
    """
    manager = SessionManager()

    try:
        message_view_datas, message = manager.get_conversation_views(session_id=session_id)

        return make_response(True, data=message_view_datas, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
