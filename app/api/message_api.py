from flask import Blueprint, request

from app.service.message_service import (
    delete_message,
    get_all_messages,
    get_message,
    handle_user_message,
)
from app.toolkit.api_tool import BaseException, make_response

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/<int:session_id>", methods=["GET"])
def get_messages(session_id):
    try:
        messages = get_all_messages(session_id)
        return make_response(True, messages)
    except BaseException as e:
        return make_response(False, message=str(e))


@messages_bp.route("/", methods=["POST"])
def create_message():
    data = request.json
    session_id = data.get("session_id")
    message_content = data.get("message")

    try:
        response = handle_user_message(session_id, message_content)
        return make_response(True, response)
    except BaseException as e:
        return make_response(False, message=str(e))


@messages_bp.route("/<int:message_id>", methods=["GET"])
def get_message_by_id(message_id):
    try:
        message = get_message(message_id)
        return make_response(True, message)
    except BaseException as e:
        return make_response(False, message=str(e))


@messages_bp.route("/<int:message_id>", methods=["DELETE"])
def delete_message_by_id(message_id):
    try:
        result = delete_message(message_id)
        return make_response(True, message=result["message"])
    except BaseException as e:
        return make_response(False, message=str(e))
