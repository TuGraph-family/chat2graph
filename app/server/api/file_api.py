import os
from pathlib import Path
from flask import Blueprint, request
from werkzeug.utils import secure_filename

from app.server.common.util import BaseException, make_response
from dotenv import load_dotenv

load_dotenv()
files_bp = Blueprint("files", __name__)


@files_bp.route("/<string:knowledge_base_id>/upload", methods=["POST"])
def upload_file(knowledge_base_id):
    """
    Upload a file to the server.
    """

    if "file" not in request.files:
        raise BaseException("No file part in the request")

    file = request.files["file"]

    if file.filename == "":
        raise BaseException("No selected file")

    try:
        UPLOAD_FOLDER = Path(os.getenv("APP_ROOT", f"{os.getcwd()}/files/"))

        kb_folder = UPLOAD_FOLDER / knowledge_base_id
        safe_filename = file.filename
        file_path = kb_folder / safe_filename

        if file_path.exists():
            raise BaseException(
                f"File '{safe_filename}' already exists in knowledge base '{knowledge_base_id}'."
            )

        kb_folder.mkdir(parents=True, exist_ok=True)

        file.save(file_path)

        project_root = Path(os.getcwd())
        relative_path = file_path.relative_to(project_root)

        return make_response(
            True,
            data={"filename": safe_filename, "relative_path": str(relative_path)},
            message="File uploaded successfully",
        )

    except Exception as e:
        raise BaseException(f"Failed to upload file: {str(e)}") from e


@files_bp.route("/<string:knowledge_base_id>/delete/<string:filename>", methods=["DELETE"])
def delete_file(knowledge_base_id, filename):
    """
    Delete a file from the server within a specific knowledge base.
    """
    UPLOAD_FOLDER = Path(os.getenv("APP_ROOT", f"{os.getcwd()}/files"))

    kb_folder = UPLOAD_FOLDER / knowledge_base_id
    file_path = kb_folder / filename

    if not file_path.exists():
        raise BaseException(f"File '{filename}' not found in knowledge base '{knowledge_base_id}'.")

    try:
        file_path.unlink()

        return make_response(
            True,
            message=f"File '{filename}' deleted successfully from knowledge base '{knowledge_base_id}'.",
        )
    except Exception as e:
        raise BaseException(f"Failed to delete file: {str(e)}") from e
