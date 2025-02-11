from app.plugin.sqlite.sqlite_model import Message, db
from app.server.common.api_tool import ParameterException, ServiceException
from datetime import datetime, timezone
from openai import OpenAI
import os



PROXY_API_KEY = os.getenv('PROXY_API_KEY')
PROXY_SERVER_URL = os.getenv('PROXY_SERVER_URL')
PROXYLLM_BACKEND = os.getenv('PROXYLLM_BACKEND')
client = OpenAI(api_key=PROXY_API_KEY,base_url=PROXY_SERVER_URL)

def get_all_messages(session_id):
    messages = Message.query.filter_by(session_id=session_id).all()
    return [
        {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "message": message.message,
            "timestamp": message.timestamp.isoformat()
        } for message in messages
    ]

def create_message(session_id, role, message_content):
    if not role or not message_content:
        raise ParameterException("Message content are required")
    
    new_message = Message(
        session_id=session_id,
        role=role,
        message=message_content,
        timestamp=datetime.now(timezone.utc)
    )
    
    try:
        db.session.add(new_message)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ServiceException(f"Failed to create message: {str(e)}")
    
    return {
        "id": new_message.id,
        "session_id": new_message.session_id,
        "role": new_message.role,
        "message": new_message.message,
        "timestamp": new_message.timestamp.isoformat()
    }

def get_message(message_id):
    message = Message.query.get(message_id)
    if message is None:
        raise ParameterException("Message not found")
    
    return {
        "id": message.id,
        "session_id": message.session_id,
        "role": message.role,
        "message": message.message,
        "timestamp": message.timestamp.isoformat()
    }

def delete_message(message_id):
    message = Message.query.get(message_id)
    if message is None:
        raise ParameterException("Message not found")
    try:
        db.session.delete(message)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ServiceException(f"Failed to delete message: {str(e)}")
    
    return {"message": "Message deleted successfully"}

def handle_user_message(session_id, user_message):
    user_message_data = create_message(session_id, 'user', user_message)
    model_response = call_model(session_id, user_message)
    assistant_message_data = create_message(session_id, 'system', model_response)
    return {
        "user_message": user_message_data,
        "assistant_message": assistant_message_data
    }

def call_model(session_id, user_message):
    try:
        completion = client.chat.completions.create(
            model=PROXYLLM_BACKEND,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        answer = completion.choices[0].message
        return answer.content
    except Exception as e:
        error_message = f"Failed to call OpenAI API: {str(e)}"
        create_message(session_id, 'system', error_message)
        raise ServiceException(error_message)
