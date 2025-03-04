import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from app.core.dal.database import init_db
from app.server.api import register_blueprints
from app.server.common.util import BaseException, make_error_response


def create_app():
    static_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    app = Flask(__name__, static_folder=static_folder_path)

    @app.route("/")
    def serve_index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:filename>")
    def serve_static(filename):
        try:
            return send_from_directory(app.static_folder, filename)
        except:  # noqa: E722
            return send_from_directory(app.static_folder, "index.html")

    CORS(app)

    register_blueprints(app)

    @app.errorhandler(BaseException)
    def handle_base_exception(e):
        return make_error_response(e.status_code, e.message)

    with app.app_context():
        init_db()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)
