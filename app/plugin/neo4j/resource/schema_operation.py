from asyncio import Lock
import json
import os
import tempfile
from typing import Any, Dict, List

from werkzeug.datastructures import FileStorage

from app.core.common.system_env import SystemEnv
from app.core.service.file_service import FileService

schema_file_lock = Lock()


class SchemaManager:
    """Manager the schema json of the graph database."""

    @staticmethod
    async def read_schema(file_service: FileService) -> Dict[str, Any]:
        """Read the schema file."""

        async with schema_file_lock:
            try:
                schema_files = SchemaManager._find_schema_files(file_service)
                if schema_files:
                    # use the latest schema file
                    file_content = file_service.read_file(schema_files[-1])
                    return json.loads(file_content)

                return {"nodes": {}, "relationships": {}}
            except Exception as e:
                print(f"Error reading schema: {e}")
                return {"nodes": {}, "relationships": {}}

    @staticmethod
    async def write_schema(file_service: FileService, schema: Dict[str, Any]) -> None:
        """Write the schema file using file_service's upload_file method."""
        # first, try to read existing schema1
        existing_schema = await SchemaManager.read_schema(file_service)

        async with schema_file_lock:
            # merge with new schema (this will override existing data with new data)
            if isinstance(schema, dict) and isinstance(existing_schema, dict):
                if "nodes" in schema and "nodes" in existing_schema:
                    existing_schema["nodes"].update(schema["nodes"])
                if "relationships" in schema and "relationships" in existing_schema:
                    existing_schema["relationships"].update(schema["relationships"])
                # update other top-level keys
                for key in schema:
                    if key not in ["nodes", "relationships"]:
                        existing_schema[key] = schema[key]
            else:
                # if not a dict or structure is different, just use the new schema
                existing_schema = schema

            # create a temporary file to store the updated schema
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as temp_file:
                json.dump(existing_schema, temp_file, indent=2, ensure_ascii=False)
                temp_file_path = temp_file.name

            try:
                # create a FileStorage object from the temporary file
                with open(temp_file_path, "rb") as f:
                    file_storage = FileStorage(
                        stream=f,
                        filename=SystemEnv.SCHEMA_FILE_NAME,
                        content_type="application/json",
                    )

                    # upload the file using file_service with the schema file ID
                    file_service.upload_or_update_file(
                        file_storage, file_id=SystemEnv.SCHEMA_FILE_ID
                    )
            finally:
                # remove the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

    @staticmethod
    def _find_schema_files(file_service: FileService) -> List[str]:
        """Find all schema files id by querying the file_service."""
        return [SystemEnv.SCHEMA_FILE_ID]

    @staticmethod
    def schema_to_graph_dict(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert the graph database schema into a Graph dict that conforms to the
            GraphMessage format.

        Args:
            schema (Dict[str, Any]): The graph database schema dictionary

        Returns:
            A Graph dict that conforms to the GraphMessage format
        """
        graph_dict: Dict[str, Any] = {"vertices": [], "edges": []}

        # 处理节点
        for node_label, node_info in schema.get("nodes", {}).items():
            vertex = {
                "id": node_label,
                "label": node_label,
                "properties": {
                    "primary_key": node_info.get("primary_key", ""),
                    "property_definitions": [
                        prop.get("name") for prop in node_info.get("properties", [])
                    ],
                },
            }
            graph_dict["vertices"].append(vertex)

        # 处理关系
        for rel_label, rel_info in schema.get("relationships", {}).items():
            # 获取源节点和目标节点标签列表
            source_labels = rel_info.get("source_vertex_labels", [])
            target_labels = rel_info.get("target_vertex_labels", [])

            # 为每对可能的源节点和目标节点组合创建一条边
            for source_label in source_labels:
                for target_label in target_labels:
                    edge = {
                        "source": source_label,
                        "target": target_label,
                        "label": rel_label,
                        "properties": {
                            "primary_key": rel_info.get("primary_key", ""),
                            "property_definitions": [
                                prop.get("name") for prop in rel_info.get("properties", [])
                            ],
                        },
                    }
                    graph_dict["edges"].append(edge)

        return graph_dict
