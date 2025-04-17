from app.server.api.file_api import files_bp
from app.server.api.graph_db_api import graph_dbs_bp
from app.server.api.job_api import jobs_bp
from app.server.api.knowledge_base_api import knowledgebases_bp
from app.server.api.session_api import sessions_bp


def register_blueprints(app):
    """Register all blueprints."""
    app.register_blueprint(sessions_bp, url_prefix="/api/sessions")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(graph_dbs_bp, url_prefix="/api/graphdbs")
    app.register_blueprint(files_bp, url_prefix="/api/files")
    app.register_blueprint(knowledgebases_bp, url_prefix="/api/knowledgebases")
