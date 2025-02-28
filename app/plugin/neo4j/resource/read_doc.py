from asyncio import Lock
import json
import os
from typing import Dict

schema_file_lock = Lock()


class SchemaManager:
    """Manager the schema json of the graph database."""

    SCHEMA_FILE = ".schema.json"

    @staticmethod
    async def read_schema() -> Dict:
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
    async def write_schema(schema: Dict):
        """Write the schema file."""
        async with schema_file_lock:
            with open(SchemaManager.SCHEMA_FILE, "w", encoding="utf-8") as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
