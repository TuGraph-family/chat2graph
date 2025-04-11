from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from app.core.model.artifact import (
    Artifact,
    ArtifactMetadata,
    ArtifactStatus,
    ContentType,
    SourceReference,
)
from app.core.service.artifact_service import ArtifactService
from app.core.service.file_service import FileService
from app.core.service.graph_db_service import GraphDbService
from app.core.toolkit.tool import Tool
from app.plugin.neo4j.resource.schema_operation import SchemaManager


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


class VertexLabelAdder(Tool):
    """Tool for generating Cypher statements to create vertex labels in Neo4j."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.create_and_import_vertex_label_schema.__name__,
            description=self.create_and_import_vertex_label_schema.__doc__ or "",
            function=self.create_and_import_vertex_label_schema,
        )

    async def create_and_import_vertex_label_schema(
        self,
        file_service: FileService,
        graph_db_service: GraphDbService,
        artifact_service: ArtifactService,
        session_id: str,
        job_id: str,
        label: str,
        properties: List[Dict[str, Union[str, bool]]],
        primary: str = "id",
    ) -> str:
        """Create and import a vertex label in Neo4j with specified properties.

        This function defines a new vertex label (node type) in the Neo4j graph database,
        establishing its property schema and primary key.

        Args:
            session_id (str): The session ID for the current session.
            job_id (str): The job ID for the current job.
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

        store = graph_db_service.get_default_graph_db()
        with store.conn.session() as session:
            for statement in statements:
                print(f"Executing statement: {statement}")
                session.run(statement)

            # update schema file
            schema = await SchemaManager.read_schema(file_service=file_service)
            schema["nodes"][label] = {"primary_key": primary, "properties": property_details}
            await SchemaManager.write_schema(file_service=file_service, schema=schema)

            schema_graph_dict: Dict[str, Any] = SchemaManager.schema_to_graph_dict(schema)
            # save the graph artifact
            artifacts: List[Artifact] = artifact_service.get_artifacts_by_job_id_and_type(
                job_id=job_id, content_type=ContentType.GRAPH
            )

            if len(artifacts) == 0:
                artifact = Artifact(
                    content_type=ContentType.GRAPH,
                    content=schema_graph_dict,
                    source_reference=SourceReference(job_id=job_id, session_id=session_id),
                    status=ArtifactStatus.FINISHED,
                    metadata=ArtifactMetadata(
                        version=1, description="It is the database schema graph."
                    ),
                )
                artifact_service.save_artifact(artifact=artifact)
            else:
                artifact_service.increment_and_save(
                    artifact=artifacts[0], new_content=schema_graph_dict
                )

            return f"Successfully created label {label}"


class EdgeLabelAdder(Tool):
    """Tool for generating Cypher statements to create edge labels in GraphDB."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.create_and_import_edge_label_schema.__name__,
            description=self.create_and_import_edge_label_schema.__doc__ or "",
            function=self.create_and_import_edge_label_schema,
        )

    async def create_and_import_edge_label_schema(
        self,
        file_service: FileService,
        graph_db_service: GraphDbService,
        artifact_service: ArtifactService,
        session_id: str,
        job_id: str,
        label: str,
        properties: List[Dict[str, Union[str, bool]]],
        source_vertex_labels: List[str],
        target_vertex_labels: List[str],
        primary: str = "id",
    ) -> str:
        """Create and import a relationship type in Neo4j using specified properties and endpoint constraints.

        This function defines a new relationship type in the Neo4j graph database,
        establishing its property schema, primary key, and valid node label pairs
        for the relationship endpoints.

        Args:
            session_id (str): The session ID for the current session.
            job_id (str): The job ID for the current job.
            label (str): The label name of the relationship type. It will be automatically
                converted to uppercase according to Neo4j conventions.
            properties (List[Dict[str, Union[str, bool]]]): Property definitions for the
                relationship type. Each property is defined as a dictionary containing:
                    - name (str): Property name
                    - type (str): Data type (e.g., 'STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'DATE', 'DATETIME')
                    - index (bool): Whether to create an index for this property (default: True)
            source_vertex_labels (List[str]): List of allowed source node labels.
            target_vertex_labels (List[str]): List of allowed target node labels.
            primary (str): The property name used as a unique identifier. Must be unique within the relationship type (default: 'id').

        Returns:
            str: A status message indicating successful creation of the relationship type,
                including details about constraints and indexes,
                as well as endpoint label restrictions stored in the schema.

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
                "WORKS_AT",
                properties,
                source_vertex_labels=["Person"],
                target_vertex_labels=["Company", "Organization"],
                "id"
            )
            # Expected result: Schema updated with WORKS_AT relationship allowing
            # (Person)-[:WORKS_AT]->(Company) and (Person)-[:WORKS_AT]->(Organization)
            # and constraints/indexes created for properties 'id' and 'role'.
            ```
        """  # noqa: E501
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

        # execute Cypher statements in Neo4j
        # note: Neo4j does not support directly restricting the node label types at both ends of a
        # relationship through Cypher DDL. Such restrictions are typically expressed and enforced
        # at the application level or through schema definitions.
        # here, we will store this restriction information in the schema file.
        store = graph_db_service.get_default_graph_db()
        with store.conn.session() as session:
            for statement in statements:
                print(f"Executing statement: {statement}")
                session.run(statement)

        # update schema file
        schema = await SchemaManager.read_schema(file_service=file_service)
        if "relationships" not in schema:
            schema["relationships"] = {}

        # store relationship type information in the schema, including endpoint label constraints.
        schema["relationships"][label] = {
            "primary_key": primary,
            "properties": property_details,
            "source_vertex_labels": source_vertex_labels,
            "target_vertex_labels": target_vertex_labels,
        }
        await SchemaManager.write_schema(file_service=file_service, schema=schema)

        # save the graph artifact
        schema_graph_dict: Dict[str, Any] = SchemaManager.schema_to_graph_dict(schema)
        artifacts: List[Artifact] = artifact_service.get_artifacts_by_job_id_and_type(
            job_id=job_id, content_type=ContentType.GRAPH
        )
        if len(artifacts) == 0:
            artifact = Artifact(
                content_type=ContentType.GRAPH,
                content=schema_graph_dict,
                source_reference=SourceReference(job_id=job_id, session_id=session_id),
                status=ArtifactStatus.FINISHED,
                metadata=ArtifactMetadata(
                    version=1, description="It is the database schema graph."
                ),
            )
            artifact_service.save_artifact(artifact=artifact)
        else:
            artifact_service.increment_and_save(
                artifact=artifacts[0], new_content=schema_graph_dict
            )

        return (
            f"Successfully configured relationship type {label} in schema "
            f"(Source: {source_vertex_labels}, Target: {target_vertex_labels}) "
            f"and created constraints/indexes in Neo4j."
        )


class GraphReachabilityGetter(Tool):
    """Tool for getting the reachability information of the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.calculate_and_get_graph_reachability.__name__,
            description=self.calculate_and_get_graph_reachability.__doc__ or "",
            function=self.calculate_and_get_graph_reachability,
        )

    async def calculate_and_get_graph_reachability(self, graph_db_service: GraphDbService) -> str:
        """Calculate and get the reachability information of the graph database which can help to
            understand the graph schema structure.

        Args:
            None args required

        Returns:
            str: The reachability of the graph database in string format
        """
        store = graph_db_service.get_default_graph_db()
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
