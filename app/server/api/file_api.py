import os
from flask import Blueprint, request
from werkzeug.utils import secure_filename

from app.server.common.util import BaseException, make_response

files_bp = Blueprint("files", __name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@files_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Upload a file to the server.
    """
    if "file" not in request.files:
        raise BaseException("No file part in the request")

    file = request.files["file"]

    if file.filename == "":
        raise BaseException("No selected file")

    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        project_root = os.getcwd()
        relative_path = os.path.relpath(file_path, project_root)
        return make_response(
            True,
            data={"filename": file.filename, "relative_path": relative_path},
            message="File uploaded successfully",
        )
    except Exception as e:
        raise BaseException(f"Failed to upload file: {str(e)}") from e


@files_bp.route("/delete/<string:filename>", methods=["DELETE"])
def delete_file(filename):
    """
    Delete a file from the server.
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        raise BaseException("File not found")

    try:
        os.remove(file_path)
        return make_response(True, message=f"File '{filename}' deleted successfully")
    except Exception as e:
        raise BaseException(f"Failed to delete file: {str(e)}") from e
