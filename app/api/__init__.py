from .sessions import sessions_bp
from .messages import messages_bp

def register_blueprints(app):
    app.register_blueprint(sessions_bp, url_prefix='/api/sessions')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')