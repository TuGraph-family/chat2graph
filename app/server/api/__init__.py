from app.server.api.graphdb_api import graphdbs_bp
from app.server.api.knowledgebase_api import knowledgebases_bp
from app.server.api.message_api import messages_bp
from app.server.api.session_api import sessions_bp
from app.server.api.file_api import files_bp


def register_blueprints(app):
    app.register_blueprint(sessions_bp, url_prefix="/api/sessions")
    app.register_blueprint(messages_bp, url_prefix="/api/messages")
    app.register_blueprint(graphdbs_bp, url_prefix="/api/graphdbs")
    app.register_blueprint(files_bp, url_prefix="/api/files")
    app.register_blueprint(knowledgebases_bp, url_prefix="/api/knowledgebases")
