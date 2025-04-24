from typing import Any, Dict, List, Optional, Set, Union
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
from app.plugin.neo4j.resource.data_importation import update_graph_artifact


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
            schema = graph_db_service.get_schema_metadata(
                graph_db_config=graph_db_service.get_default_graph_db_config()
            )
            schema["nodes"][label] = {"primary_key": primary, "properties": property_details}
            graph_db_service.update_schema_metadata(
                graph_db_config=graph_db_service.get_default_graph_db_config(),
                schema=schema,
            )

            schema_graph_dict: Dict[str, Any] = graph_db_service.schema_to_graph_dict(
                graph_db_config=graph_db_service.get_default_graph_db_config()
            )

            # save the graph artifact
            update_graph_artifact(
                artifact_service=artifact_service,
                session_id=session_id,
                job_id=job_id,
                data_graph_dict=schema_graph_dict,
                description="It is the database schema graph.",
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
        for the relationship endpoints. It first validates if the specified source
        and target node labels exist in the current schema.

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
            source_vertex_labels (List[str]): List of allowed source node labels. (please make sure the node labels has been created in the current schema)
            target_vertex_labels (List[str]): List of allowed target node labels. (please make sure the node labels has been created in the current schema)
            primary (str): The property name used as a unique identifier. Must be unique within the relationship type (default: 'id').

        Returns:
            str: A status message indicating successful creation of the relationship type,
                including details about constraints and indexes, and endpoint label restrictions stored in the schema.
                Or, an error message if source or target node labels are not found in the existing schema.

        Example:
            ```python
            # assuming 'Person', 'Company' exist, but 'Organization' does not
            properties = [{"name": "role", "type": "STRING", "index": True}]
            result = await create_edge_label_by_json_schema(
                "WORKS_AT",
                properties,
                source_vertex_labels=["Person"],
                target_vertex_labels=["Company", "Organization"], # 'Organization' is missing
                "id"
            )
            # expected result: "Error: Cannot create relationship 'WORKS_AT'. The following node labels are not defined in the schema: ['Organization']. Please define these node labels first."
            ```
        """  # noqa: E501
        # validate the schema before creating the edge label
        try:
            schema = graph_db_service.get_schema_metadata(
                graph_db_config=graph_db_service.get_default_graph_db_config()
            )
            existing_node_labels = set(schema.get("nodes", {}).keys())

            required_labels = set(source_vertex_labels) | set(target_vertex_labels)
            missing_labels = required_labels - existing_node_labels

            if missing_labels:
                error_message = (
                    f"Error: Cannot create relationship '{label.upper()}'. "
                    f"The following node labels are not defined in the schema: "
                    f"{sorted(missing_labels)}. Please define these node labels first using "
                    "the appropriate tool (like VertexLabelAdder)."
                )
                print(f"Warning: validation failed for EdgeLabelAdder: {error_message}")
                return error_message

        except Exception as e:
            return (
                f"Error: Failed to validate schema before creating edge '{label.upper()}'. "
                f"Details: {e}"
            )
        # end of validation

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
        schema = graph_db_service.get_schema_metadata(
            graph_db_config=graph_db_service.get_default_graph_db_config()
        )
        if "relationships" not in schema:
            schema["relationships"] = {}

        # store relationship type information in the schema, including endpoint label constraints.
        schema["relationships"][label] = {
            "primary_key": primary,
            "properties": property_details,
            "source_vertex_labels": source_vertex_labels,
            "target_vertex_labels": target_vertex_labels,
        }
        graph_db_service.update_schema_metadata(
            graph_db_config=graph_db_service.get_default_graph_db_config(),
            schema=schema,
        )

        # save the graph artifact
        schema_graph_dict: Dict[str, Any] = graph_db_service.schema_to_graph_dict(
            graph_db_config=graph_db_service.get_default_graph_db_config()
        )
        artifacts: List[Artifact] = artifact_service.get_artifacts_by_job_id_and_type(
            job_id=job_id,
            content_type=ContentType.GRAPH,
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
                artifact=artifacts[0],
                new_content=schema_graph_dict,
            )

        # final success message
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
        """Analyzes the graph schema reachability by checking for isolated node labels (hanging points).

        It retrieves all defined node labels and relationship types, then analyzes the
        schema visualization to identify node labels that do not participate in any
        relationships.

        Args:
            None args required

        Returns:
            str: A summary of the graph schema, highlighting any isolated node labels found.
                 Indicates potential "hanging points" in the schema structure.
        """  # noqa: E501

        # 1. Read the stored schema definition
        schema: Dict[str, Any] = graph_db_service.get_schema_metadata(
            graph_db_config=graph_db_service.get_default_graph_db_config()
        )
        if not schema:
            return "Schema definition file not found or is empty."

        nodes_schema = schema.get("nodes", {})
        relationships_schema = schema.get("relationships", {})

        # 2. Get all defined node labels from the schema
        all_defined_node_labels: Set[str] = set(nodes_schema.keys())

        # 3. Get all defined relationship types from the schema
        all_defined_relationship_types: Set[str] = set(relationships_schema.keys())

        # 4. Identify connected node labels and check for hanging edge definitions
        connected_node_labels: Set[str] = set()
        hanging_edge_definitions: List[str] = []
        schema_connections: List[str] = []  # descriptions like (:LabelA)-[:REL]->(:LabelB)

        for rel_type, rel_info in relationships_schema.items():
            source_labels = rel_info.get("source_vertex_labels", [])
            target_labels = rel_info.get("target_vertex_labels", [])

            # add labels involved in this relationship to the connected set
            connected_node_labels.update(source_labels)
            connected_node_labels.update(target_labels)

            # build connection description string
            schema_connections.append(f"(:{source_labels})-[:{rel_type}]->(:{target_labels})")

            # check if source labels are defined node types
            for src_label in source_labels:
                if src_label not in all_defined_node_labels:
                    hanging_edge_definitions.append(
                        f"- Relationship '{rel_type}' "
                        f"uses undefined source node label: '{src_label}'"
                    )

            # check if target labels are defined node types
            for tgt_label in target_labels:
                if tgt_label not in all_defined_node_labels:
                    hanging_edge_definitions.append(
                        f"- Relationship '{rel_type}' "
                        f"uses undefined target node label: '{tgt_label}'"
                    )

        # 5. Identify isolated node labels (hanging points)
        # these are node labels defined in schema['nodes'] but not used in any relationship
        isolated_labels = all_defined_node_labels - connected_node_labels

        # 6. Construct the report string
        report_lines = [
            "Stored Graph Schema Analysis:",
            f"- Defined Node Labels: {sorted(all_defined_node_labels)}",
            f"- Defined Relationship Types: {sorted(all_defined_relationship_types)}",
            f"- Defined Connections Count: {len(schema_connections)}",
            # uncomment below to see example connections from schema definition
            "  - Example Defined Connections: (showing first 10)",
            *[f"    {conn}" for conn in schema_connections[:10]],
            ("    ..." if len(schema_connections) > 10 else ""),
        ]

        issues_found = False
        if isolated_labels:
            issues_found = True
            report_lines.append("\nPotential Connectivity Issues (Hanging Points):")
            report_lines.append(f"  - Isolated Node Labels: {sorted(isolated_labels)}")
            report_lines.append(
                "    Reason: These node labels are defined in the schema ('nodes' section) "
                "but are not listed as a source or target for any defined relationship "
                "in the schema ('relationships' section)."
            )

        if hanging_edge_definitions:
            issues_found = True
            report_lines.append("\nPotential Consistency Issues (Hanging Edge Definitions):")
            report_lines.extend(hanging_edge_definitions)
            report_lines.append(
                "    Reason: These relationships are defined to connect node labels "
                "that do not have a corresponding definition in the schema's 'nodes' section."
            )

        if not issues_found:
            report_lines.append(
                "\nSchema Status: No isolated nodes or inconsistent relationship definitions "
                "found in the stored schema. The reachability of graph is good."
            )

        return "\n".join(report_lines)
