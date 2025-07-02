import json
import traceback
from typing import Any, Dict, List, Set

from neo4j.graph import Node, Path, Relationship

from app.core.service.artifact_service import ArtifactService
from app.core.service.graph_db_service import GraphDbService
from app.core.toolkit.tool import Tool
from app.plugin.neo4j.resource.data_importation import update_graph_artifact


class CypherExecutor(Tool):
    """Tool for executing Cypher queries in Neo4j."""

    def __init__(self):
        super().__init__(
            name=self.execute_cypher.__name__,
            description=self.execute_cypher.__doc__ or "",
            function=self.execute_cypher,
        )

    async def execute_cypher(
        self,
        graph_db_service: GraphDbService,
        artifact_service: ArtifactService,
        session_id: str,
        job_id: str,
        cypher_query: str,
    ) -> str:
        """Execute a Cypher query directly against the Neo4j database.

        Args:
            session_id (str): The session ID
            job_id (str): The job ID
            cypher_query (str): The Cypher query to execute

        Returns:
            str: Query execution results

        Examples:
            >>> cypher_query = "MATCH (n:Character) WHERE n.name CONTAINS 'Tech' RETURN n LIMIT 10"
            >>> result = await executor.execute_cypher("session_id_xxx", "job_id_xxx", cypher_query)
        """
        store = graph_db_service.get_default_graph_db()
        text_results = []  # for the textual representation
        # initialize graph data following the standard structure
        graph_data: Dict[str, List[Dict[str, Any]]] = {
            "vertices": [],
            "edges": [],
        }
        # keep track of processed elements to avoid duplicates in graph_data
        processed_nodes: Set[str] = set()
        processed_rels: Set[str] = set()

        # fetch schema
        schema = graph_db_service.get_schema_metadata(
            graph_db_config=graph_db_service.get_default_graph_db_config()
        )
        node_schema = schema.get("nodes", {})

        with store.conn.session() as session:
            try:
                result = session.run(cypher_query)
                records = list(result)  # consume the result iterator

                # process each record to extract nodes and relationships
                for record in records:
                    for value in record.values():
                        _process_value(
                            value, graph_data, node_schema, processed_nodes, processed_rels
                        )

                # build a textual representation of the results
                for record in records:  # iterate again for text formatting
                    record_dict = {}
                    for key, value in record.items():
                        if isinstance(value, Node):
                            node_id = value.element_id if hasattr(value, "element_id") else value.id
                            label = list(value.labels)[0] if value.labels else "Unknown"
                            props = dict(value.items())
                            record_dict[key] = f"({node_id}:{label} {props})"
                        elif isinstance(value, Relationship):
                            rel_id = value.element_id if hasattr(value, "element_id") else value.id
                            props = dict(value.items())
                            # simplified text representation
                            record_dict[key] = f"[:{value.type} {{id: {rel_id}, props: {props}}}]"
                        elif isinstance(value, Path):
                            # simple path representation for text
                            record_dict[key] = " -> ".join(
                                [f"({n.element_id})" for n in value.nodes]
                            )
                        else:
                            # handle primitive values or other complex types as strings
                            try:
                                record_dict[key] = json.dumps(value, ensure_ascii=False)
                            except TypeError:
                                record_dict[key] = str(value)
                    text_results.append(str(record_dict))

                if graph_data["vertices"] or graph_data["edges"]:
                    update_graph_artifact(
                        artifact_service=artifact_service,
                        session_id=session_id,
                        job_id=job_id,
                        data_graph_dict=graph_data,
                        description="Graph generated from Cypher query results.",
                    )

                if not text_results:
                    result_str = "没有查询到数据。"
                else:
                    result_str = "\n".join(text_results)  # use the formatted text results

                # include GraphJSON in the final string output
                graph_json_str = json.dumps(graph_data, indent=4, ensure_ascii=False)
                return (
                    f"Cypher查询执行成功。\n查询语句：\n{cypher_query}\n查询结果：\n{result_str}\n"
                    f"GraphJSON：\n{graph_json_str}"
                )

            except Exception as e:
                tb_str = traceback.format_exc()
                print(f"Cypher query failed: {e}\n{tb_str}")  # optional: log the error server-side
                return (
                    f"Cypher查询执行失败: {str(e)}\n查询语句：\n{cypher_query}\n"
                    f"Traceback:\n{tb_str}"
                )


def _get_node_alias(node: Node, node_schema: Dict[str, Any]) -> str:
    """Determines the alias for a node based on the schema's primary key."""
    node_id = node.element_id if hasattr(node, "element_id") else str(node.id)
    alias = node_id  # default alias
    properties = dict(node.items())
    if node.labels:
        label = list(node.labels)[0]
        primary_key_prop = node_schema.get(label, {}).get("primary_key")
        if primary_key_prop and primary_key_prop in properties:
            alias = properties[primary_key_prop]
    return str(alias)


def _add_node_to_graph(
    node: Node,
    graph_data: Dict[str, List[Dict[str, Any]]],
    node_schema: Dict[str, Any],
    processed_nodes: Set[str],
) -> None:
    """Adds a node to the graph_data if not already present."""
    node_id = node.element_id if hasattr(node, "element_id") else str(node.id)
    if node_id not in processed_nodes:
        label = list(node.labels)[0] if node.labels else ""
        properties = dict(node.items())
        alias = _get_node_alias(node, node_schema)
        graph_data["vertices"].append(
            {
                "id": node_id,
                "label": label,
                "alias": alias,
                "properties": properties,
            }
        )
        processed_nodes.add(node_id)


def _add_relationship_to_graph(
    rel: Relationship,
    graph_data: Dict[str, List[Dict[str, Any]]],
    node_schema: Dict[str, Any],
    processed_nodes: Set[str],
    processed_rels: Set[str],
) -> None:
    """Adds a relationship and its nodes to graph_data if not already present."""
    rel_id = rel.element_id if hasattr(rel, "element_id") else str(rel.id)
    if rel_id not in processed_rels:
        start_node = rel.start_node
        end_node = rel.end_node

        # check if start_node and end_node are valid Node objects
        if start_node is None or end_node is None:
            print(f"Warning: Skipping relationship {rel_id} due to missing start/end node.")
            return

        start_id = (
            start_node.element_id if hasattr(start_node, "element_id") else str(start_node.id)
        )
        end_id = end_node.element_id if hasattr(end_node, "element_id") else str(end_node.id)
        properties = dict(rel.items())
        alias = str(properties.get("id", rel.type))  # default alias for relationship

        # ensure start and end nodes are added
        _add_node_to_graph(start_node, graph_data, node_schema, processed_nodes)
        _add_node_to_graph(end_node, graph_data, node_schema, processed_nodes)

        graph_data["edges"].append(
            {
                "id": rel_id,
                "source": start_id,
                "target": end_id,
                "label": rel.type,
                "alias": alias,
                "properties": properties,
            }
        )
        processed_rels.add(rel_id)


def _process_value(
    value: Any,
    graph_data: Dict[str, List[Dict[str, Any]]],
    node_schema: Dict[str, Any],
    processed_nodes: Set[str],
    processed_rels: Set[str],
) -> None:
    """Recursively processes values from query results to populate graph_data."""
    if isinstance(value, Node):
        _add_node_to_graph(value, graph_data, node_schema, processed_nodes)
    elif isinstance(value, Relationship):
        _add_relationship_to_graph(value, graph_data, node_schema, processed_nodes, processed_rels)
    elif isinstance(value, Path):
        for node in value.nodes:
            _add_node_to_graph(node, graph_data, node_schema, processed_nodes)
        for rel in value.relationships:
            _add_relationship_to_graph(
                rel, graph_data, node_schema, processed_nodes, processed_rels
            )
    elif isinstance(value, list):
        for item in value:
            _process_value(item, graph_data, node_schema, processed_nodes, processed_rels)
    elif isinstance(value, dict):
        for item_value in value.values():
            _process_value(item_value, graph_data, node_schema, processed_nodes, processed_rels)
    # ignore primitive types for graph_data
