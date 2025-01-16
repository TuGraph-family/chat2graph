from app.model.sqlite_model import Session, db
from app.toolkit.api_tool import ParameterException, ServiceException

def get_all_sessions():
    sessions = Session.query.all()
    return [
        {
            "id": session.id,
            "created_at": session.created_at.isoformat(),
            "name": session.name
        } for session in sessions
    ]

def create_session(name=None):
    if name is None:
        raise ParameterException("Session name is required")
    new_session = Session(name=name)
    try:
        db.session.add(new_session)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ServiceException(f"Failed to create session: {str(e)}")
    return {
        "id": new_session.id,
        "created_at": new_session.created_at.isoformat(),
        "name": new_session.name
    }

def get_session(session_id):
    session = Session.query.get(session_id)
    if session is None:
        raise ParameterException("Session not found", 404)
    return {
        "id": session.id,
        "created_at": session.created_at.isoformat(),
        "name": session.name
    }

def delete_session(session_id):
    session = Session.query.get(session_id)
    if session is None:
        raise ParameterException("Session not found", 404)
    try:
        db.session.delete(session)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ServiceException(f"Failed to delete session: {str(e)}")
    return {"message": "Session deleted successfully"}
