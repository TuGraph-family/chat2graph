from flask import Blueprint, request

from app.server.common.util import ApiException, make_response
from app.server.manager.file_manager import FileManager

files_bp = Blueprint("files", __name__)


@files_bp.route("/<string:session_id>", methods=["POST"])
def upload_file(session_id):
    """Upload a file to the server."""

    manager = FileManager()
    if "file" not in request.files:
        raise ApiException("No file part in the request")

    file = request.files["file"]

    if file.filename == "":
        raise ApiException("No selected file")

    try:
        result, message = manager.upload_file(file=file, session_id=session_id)
        return make_response(True, data=result, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))


@files_bp.route("/<string:file_id>/", methods=["DELETE"])
def delete_file(file_id):
    """Delete a file from the server."""

    manager = FileManager()
    try:
        result, message = manager.delete_file(id=file_id)
        return make_response(True, data=result, message=message)
    except ApiException as e:
        return make_response(False, message=str(e))
