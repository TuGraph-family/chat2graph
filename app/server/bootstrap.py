import os

from flask import Flask, send_from_directory
from flask_cors import CORS  # type: ignore
import pyfiglet  # type: ignore

from app.core.dal.init_db import init_db
from app.core.sdk.agentic_service import AgenticService
from app.server.api import register_blueprints
from app.server.common.util import make_error


def create_app():
    """Create the Flask app."""
    static_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    print(f"Web resources location: {static_folder_path}")
    app = Flask(__name__, static_folder=static_folder_path)

    with app.app_context():
        init_db()

    service = AgenticService.load()

    pyfiglet.print_figlet(service.name, font="standard")

    @app.route("/")
    def serve_index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:filename>")
    def serve_static(filename):
        try:
            return send_from_directory(app.static_folder, filename)
        except Exception:
            return send_from_directory(app.static_folder, "index.html")

    CORS(app)

    register_blueprints(app)

    @app.errorhandler(Exception)
    def handle_base_exception(e: Exception):
        return make_error(e)

    return app


if __name__ == "__main__":
    print("Starting server...")
    app = create_app()
    app.run(debug=False)
