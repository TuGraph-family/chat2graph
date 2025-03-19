import os
from flask import Blueprint, request
from werkzeug.utils import secure_filename

from app.server.common.util import ApiException, make_response
from app.core.common.system_env import SystemEnv
from app.server.manager.file_manager import FileManager

files_bp = Blueprint("files", __name__)


@files_bp.route("/", methods=["POST"])
def upload_file():
    """
    Upload a file to the server.
    """

    manager = FileManager()
    if "file" not in request.files:
        raise ApiException("No file part in the request")

    file = request.files["file"]

    if file.filename == "":
        raise ApiException("No selected file")

    try:
        result, message = manager.upload_file(file=file)
        return make_response(True, data=result, message=message)
    except Exception as e:
        raise ApiException(f"Failed to upload file: {str(e)}") from e


@files_bp.route("/<string:file_id>", methods=["DELETE"])
def delete_file(file_id):
    """
    Delete a file from the server.
    """

    manager = FileManager()
    try:
        result, message = manager.delete_file(id=file_id)
        return make_response(True, data=result, message=message)
    except Exception as e:
        raise ApiException(f"Failed to delete file: {str(e)}") from e
