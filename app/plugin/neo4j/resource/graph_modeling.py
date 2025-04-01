from typing import Dict, List, Optional, Union
from uuid import uuid4

from app.core.service.file_service import FileService
from app.core.toolkit.tool import Tool
from app.plugin.neo4j.graph_store import get_graph_db
from app.plugin.neo4j.resource.read_doc import SchemaManager


class DocumentReader(Tool):
    """Tool for analyzing document content."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.read_document.__name__,
            description=self.read_document.__doc__ or "",
            function=self.read_document,
        )

    async def read_document(self, file_service: FileService, file_id: str) -> str:
        """Read the document content given the document name and chapter name.

        Args:
            file_id (str): The ID of the file to be used to fetch the doc content.

        Returns:
            The content of the document.
        """
        return file_service.read_file(file_id=file_id)


class VertexLabelGenerator(Tool):
    """Tool for generating Cypher statements to create vertex labels in Neo4j."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.create_vertex_label_by_json_schema.__name__,
            description=self.create_vertex_label_by_json_schema.__doc__ or "",
            function=self.create_vertex_label_by_json_schema,
        )

    async def create_vertex_label_by_json_schema(
        self,
        file_service: FileService,
        label: str,
        properties: List[Dict[str, Union[str, bool]]],
        primary: str = "id",
    ) -> str:
        """Create a vertex label in Neo4j with specified properties.

        This function defines a new vertex label (node type) in the Neo4j graph database,
        establishing its property schema and primary key.

        Args:
            label (str): The label name for the vertex type. Must be a valid Neo4j label name.
            properties (List[Dict[str, Union[str, bool]]]): Property definitions for the label.
                Each property is defined as a dictionary containing:
                    - name (str): Property name
                    - type (str): Data type (e.g., 'STRING', 'INTEGER', 'FLOAT', 'BOOLEAN',
                        'DATE', 'DATETIME')
                    - index (bool): Whether to create an index for the property (default: True)
            primary (str): The property name to be used as the primary key. Must be unique
                within the label (default: 'id').

        Returns:
            str: Status message indicating successful label creation with constraint and
                index details.

        Example:
            ```python
            properties = [
                {
                    "name": "id",
                    "type": "STRING",
                    "index": True,
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "index": False,
                }
            ]
            result = await create_vertex_label_by_json_schema("Person", properties, "id")
            ```
        """

        statements = []

        statements.append(
            f"CREATE CONSTRAINT {label.lower()}_{primary}_unique IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.{primary} IS UNIQUE"
        )

        # create indexes for other properties
        for prop in properties:
            if prop.get("index", True) and prop["name"] != primary:
                statements.append(
                    f"CREATE INDEX {label}_{prop['name']}_idx IF NOT EXISTS "
                    f"FOR (n:{label}) ON (n.{prop['name']})"
                )

        # prepare schema information
        property_details = []
        for p in properties:
            property_details.append(
                {
                    "name": p["name"],
                    "type": p["type"],
                    "has_index": p.get("index", True),
                    "index_name": f"{label}_{p['name']}_idx" if p.get("index", True) else None,
                }
            )

        store = get_graph_db()
        with store.conn.session() as session:
            for statement in statements:
                print(f"Executing statement: {statement}")
                session.run(statement)

            # update schema file
            schema = await SchemaManager.read_schema(file_service=file_service)
            schema["nodes"][label] = {"primary_key": primary, "properties": property_details}
            await SchemaManager.write_schema(file_service=file_service, schema=schema)

            return f"Successfully created label {label}"


class EdgeLabelGenerator(Tool):
    """Tool for generating Cypher statements to create edge labels in TuGraph."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.create_edge_label_by_json_schema.__name__,
            description=self.create_edge_label_by_json_schema.__doc__ or "",
            function=self.create_edge_label_by_json_schema,
        )

    async def create_edge_label_by_json_schema(
        self,
        file_service: FileService,
        label: str,
        properties: List[Dict[str, Union[str, bool]]],
        primary: str = "id",
    ) -> str:
        """Create a relationship type in Neo4j with specified properties.

        This function defines a new relationship type in the Neo4j graph database,
        establishing its property schema, and valid node label pairs
        for the relationship endpoints.

        Args:
            label (str): The label name for the relationship type. Will be automatically
                converted to uppercase as per Neo4j conventions.
            properties (List[Dict[str, Union[str, bool]]]): Property definitions for the
                relationship type. Each property is defined as a dictionary containing:
                    - name (str): Property name
                    - type (str): Data type (e.g., 'STRING', 'INTEGER', 'FLOAT', 'BOOLEAN',
                        'DATE', 'DATETIME')
                    - index (bool): Whether to create an index for the property (default: True)
            primary (str): The property name to be used as the unique identifier. Must be
                unique within the relationship type (default: 'id').

        Returns:
            str: Status message indicating successful relationship type creation with
                constraint and index details.

        Example:
            ```python
            properties = [
                {
                    "name": "participate",
                    "type": "STRING",
                    "index": True,
                },
                {
                    "name": "since",
                    "type": "DATETIME",
                    "index": False,
                }
            ]
            result = await create_edge_label_by_json_schema(
                "WORKS_FOR", properties, "id"
            )
            ```
        """
        label = label.upper()
        statements = []

        # create the constraints for the relationship
        statements.append(
            f"CREATE CONSTRAINT {label.lower()}_{primary}_unique IF NOT EXISTS "
            f"FOR ()-[r:{label}]-() "
            f"REQUIRE r.{primary} IS UNIQUE"
        )

        # create indexes for other properties
        for prop in properties:
            if prop.get("index", True) and prop["name"] != primary:
                statements.append(
                    f"CREATE INDEX {label}_{prop['name']}_idx IF NOT EXISTS "
                    f"FOR ()-[r:{label}]-() ON (r.{prop['name']})"
                )

        # prepare schema information
        property_details = []
        for p in properties:
            property_details.append(
                {
                    "name": p["name"],
                    "type": p["type"],
                    "has_index": p.get("index", True),
                    "index_name": f"{label}_{p['name']}_idx" if p.get("index", True) else None,
                }
            )

        store = get_graph_db()
        with store.conn.session() as session:
            for statement in statements:
                print(f"Executing statement: {statement}")
                session.run(statement)

        # update schema file
        schema = await SchemaManager.read_schema(file_service=file_service)
        schema["relationships"][label] = {"primary_key": primary, "properties": property_details}
        await SchemaManager.write_schema(file_service=file_service, schema=schema)

        return f"Successfully configured relationship type {label}"


class GraphReachabilityGetter(Tool):
    """Tool for getting the reachability information of the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_graph_reachability.__name__,
            description=self.get_graph_reachability.__doc__ or "",
            function=self.get_graph_reachability,
        )

    async def get_graph_reachability(self) -> str:
        """Get the reachability information of the graph database which can help to understand the
        graph structure.

        Args:
            None args required

        Returns:
            str: The reachability of the graph database in string format
        """
        store = get_graph_db()
        vertex_labels: List = []
        relationship_types: List = []
        with store.conn.session() as session:
            # get all vertex labels
            result = session.run("""
                CALL db.labels() YIELD label 
                RETURN collect(label) as labels
            """)
            vertex_labels = result.single()["labels"]

            # get all relationship types and their connected node labels
            result = session.run("""
                CALL db.relationshipTypes() YIELD relationshipType
                RETURN collect(relationshipType) as types
            """)
            relationship_types = result.single()["types"]

        return (
            "Here is the schema, you have to check if there exists at least one edge label between "
            "two vertex labels! If no, create more edges to make the graph more connected.\n"
            f"Vertex labels: {vertex_labels}\nRelationship types: {relationship_types}"
        )
