from app.server.api.message_api import messages_bp
from app.server.api.session_api import sessions_bp


def register_blueprints(app):
    app.register_blueprint(sessions_bp, url_prefix='/api/sessions')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
