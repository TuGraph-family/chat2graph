from asyncio import Lock
import json
import os
from typing import Dict

from app.core.service.file_service import FileService

schema_file_lock = Lock()

# SCHEMA_FILE = ".schema.json"


# class SchemaManager:
#     """Manager the schema json of the graph database."""

#     @staticmethod
#     async def read_schema(file_service: FileService) -> Dict:
#         """Read the schema file."""
#         SCHEMA_SESSION_ID = "schema_session"

#         async with schema_file_lock:
#             try:
#                 # schema_files = SchemaManager._find_schema_files(file_service)
#                 # if schema_files:
#                 #     # Use the latest schema file
#                 #     file_content = file_service.read_file(schema_files[-1])
#                 #     return json.loads(file_content)
#                 # open file SCHEMA_FILE
#                 if os.path.exists(SCHEMA_FILE):
#                     with open(SCHEMA_FILE, encoding="utf-8") as f:
#                         return json.load(f)

#                 return {"nodes": {}, "relationships": {}}
#             except Exception:
#                 return {"nodes": {}, "relationships": {}}

#     @staticmethod
#     async def write_schema(file_service: FileService, schema: Dict) -> None:
#         """Write the schema file using file_service's upload_file method."""
#         SCHEMA_SESSION_ID = "schema_session"

#         async with schema_file_lock:
#             # create a temporary file
#             # with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as temp_file:
#             #     # Write schema to the temporary file
#             #     json.dump(schema, temp_file, indent=2, ensure_ascii=False)
#             #     temp_file_path = temp_file.name

#             try:
#                 # create a FileStorage object from the temporary file
#                 # with open(temp_file_path, "rb") as f:
#                 #     file_storage = FileStorage(
#                 #         stream=f,
#                 #         filename=SchemaManager.SCHEMA_FILE,
#                 #         content_type="application/json",
#                 #     )

#                 #     # Upload the file using file_service
#                 #     file_service.upload_file(file_storage, SchemaManager.SCHEMA_SESSION_ID)
#                 with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
#                     json.dump(schema, f, indent=2, ensure_ascii=False)

#             finally:
#                 # Remove the temporary file
#                 if os.path.exists(temp_file_path):
#                     os.unlink(temp_file_path)


#     @staticmethod
#     def _find_schema_files(file_service: FileService) -> List[str]:
#         """Find all schema files id by querying the file_service."""
#         return [SystemEnv.SCHEMA_FILE_ID]


class SchemaManager:
    """Manager the schema json of the graph database."""

    SCHEMA_FILE = ".schema.json"

    @staticmethod
    async def read_schema(file_service: FileService) -> Dict:
        """Read the schema file."""
        async with schema_file_lock:
            if (
                not os.path.exists(SchemaManager.SCHEMA_FILE)
                or os.path.getsize(SchemaManager.SCHEMA_FILE) == 0
            ):
                return {"nodes": {}, "relationships": {}}

            with open(SchemaManager.SCHEMA_FILE, encoding="utf-8") as f:
                return json.load(f)

    @staticmethod
    async def write_schema(file_service: FileService, schema: Dict):
        """Write the schema file."""
        async with schema_file_lock:
            with open(SchemaManager.SCHEMA_FILE, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
