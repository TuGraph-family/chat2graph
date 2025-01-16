from flask import Blueprint, request
from app.service.session_service import get_all_sessions, create_session as service_create_session, get_session, delete_session
from app.toolkit.api_tool import make_response, BaseException

sessions_bp = Blueprint('sessions', __name__)

@sessions_bp.route('/', methods=['GET'])
def get_sessions():
    try:
        sessions = get_all_sessions()
        return make_response(True, sessions)
    except BaseException as e:
        return make_response(False, message=str(e))

@sessions_bp.route('/', methods=['POST'])
def create_session():
    data = request.json
    try:
        new_session = service_create_session(name=data.get('name'))
        return make_response(True, new_session)
    except BaseException as e:
        return make_response(False, message=str(e))

@sessions_bp.route('/<int:session_id>', methods=['GET'])
def get_session_by_id(session_id):
    try:
        session = get_session(session_id)
        return make_response(True, session)
    except BaseException as e:
        return make_response(False, message=str(e))

@sessions_bp.route('/<int:session_id>', methods=['DELETE'])
def delete_session_by_id(session_id):
    try:
        result = delete_session(session_id)
        return make_response(True, message=result['message'])
    except BaseException as e:
        return make_response(False, message=str(e))