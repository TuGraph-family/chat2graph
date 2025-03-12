import os
from pathlib import Path
from flask import Blueprint, request
import hashlib

from app.server.common.util import BaseException, make_response
from dotenv import load_dotenv

load_dotenv()
files_bp = Blueprint("files", __name__)


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
        # 1. call file manager function
        # 2. file manager call file service insert file data
        # 3. write path(url) by md5_hash
        UPLOAD_FOLDER = Path(os.getenv("APP_ROOT", f"{os.getcwd()}/files/"))
        md5_hash = hashlib.md5(file.read()).hexdigest()
        file.seek(0)
        md5_folder = UPLOAD_FOLDER / md5_hash
        safe_filename = file.filename
        file_path = md5_folder / safe_filename

        if not md5_folder.exists():
            md5_folder.mkdir(parents=True, exist_ok=True)
            safe_filename = file.filename
            file_path = md5_folder / safe_filename
            file.save(file_path)

        else:
            safe_filename = file.filename
            file_path = md5_folder / safe_filename

        project_root = Path(os.getcwd())
        relative_path = file_path.relative_to(project_root)

        return make_response(
            True,
            data={"filename": safe_filename, "relative_path": str(relative_path)},
            message="File uploaded successfully",
        )

    except Exception as e:
        raise BaseException(f"Failed to upload file: {str(e)}") from e


@files_bp.route("/delete/<string:file_id>", methods=["DELETE"])
def delete_file(file_id):
    """
    Delete a file from the server within a specific knowledge base.
    """

    # 1. call file manager get result
    # 2. file manager call file service get file path by fileID and delete file
    # (delete data in database or delete data and file)
    # file_path.unlink()
    pass
