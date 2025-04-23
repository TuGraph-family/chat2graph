from flask import Blueprint, request

from app.server.common.util import ApiException, make_response
from app.server.manager.file_manager import FileManager

files_bp = Blueprint("files", __name__)


# TODO: modify the url pattern to avoid the anbiguity of session_id and file_id
@files_bp.route("/", methods=["POST"])
def upload_file(session_id: str):
    """Upload a file to the server."""
    manager = FileManager()

    if "file" not in request.files:
        raise ApiException("No file part in the request")

    file = request.files["file"]
    if file.filename == "":
        raise ApiException("No selected file")

    result, message = manager.upload_file(file=file)
    return make_response(data=result, message=message)


@files_bp.route("/<string:file_id>", methods=["DELETE"])
def delete_file(file_id: str):
    """Delete a file from the server."""

    manager = FileManager()
    result, message = manager.delete_file(id=file_id)
    return make_response(data=result, message=message)
