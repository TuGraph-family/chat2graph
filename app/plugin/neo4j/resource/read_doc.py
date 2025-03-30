from asyncio import Lock
import json
import os
import tempfile
from typing import Dict

from werkzeug.datastructures import FileStorage

from app.core.common.system_env import SystemEnv
from app.core.service.file_service import FileService

schema_file_lock = Lock()


class SchemaManager:
    """Manager the schema json of the graph database."""

    SCHEMA_FILE = ".schema.json"
    SCHEMA_SESSION_ID = "schema_session"

    @staticmethod
    async def read_schema(file_service: FileService) -> Dict:
        """Read the schema file."""
        async with schema_file_lock:
            try:
                schema_files = SchemaManager._find_schema_files(file_service)
                if schema_files:
                    # Use the latest schema file
                    file_content = file_service.read_file(schema_files[-1])
                    return json.loads(file_content)
                return {"nodes": {}, "relationships": {}}
            except Exception:
                return {"nodes": {}, "relationships": {}}

    @staticmethod
    async def write_schema(file_service: FileService, schema: Dict) -> None:
        """Write the schema file using file_service's upload_file method."""
        async with schema_file_lock:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as temp_file:
                # Write schema to the temporary file
                json.dump(schema, temp_file, indent=2, ensure_ascii=False)
                temp_file_path = temp_file.name

            try:
                # Create a FileStorage object from the temporary file
                with open(temp_file_path, "rb") as f:
                    file_storage = FileStorage(
                        stream=f,
                        filename=SchemaManager.SCHEMA_FILE,
                        content_type="application/json",
                    )

                    # Upload the file using file_service
                    file_service.upload_file(file_storage, SchemaManager.SCHEMA_SESSION_ID)
            finally:
                # Remove the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

    @staticmethod
    def _find_schema_files(file_service: FileService) -> list:
        """Find all schema files id by querying the file_service."""
        return [SystemEnv.SCHEMA_FILE_ID]
