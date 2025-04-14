import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.model.artifact import (
    Artifact,
    ArtifactMetadata,
    ArtifactStatus,
    ContentType,
    SourceReference,
)
from app.core.service.artifact_service import ArtifactService
from app.core.service.graph_db_service import GraphDbService
from app.core.toolkit.tool import Tool


class CypherExecutor(Tool):
    """Tool for executing Cypher queries in Neo4j."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
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
        results = []
        # Initialize graph data for Graph JSON
        graph_data: Dict[str, Any] = {
            "vertices": [],
            "edges": [],
        }

        with store.conn.session() as session:
            try:
                result = session.run(cypher_query)
                records = list(result)

                for record in records:
                    record_dict = {}
                    for key, value in record.items():
                        # Handle nodes
                        if hasattr(value, "labels") and hasattr(value, "items"):
                            # It's a node
                            node_id = value.element_id if hasattr(value, "element_id") else value.id
                            node_label = list(value.labels)[0] if value.labels else "Unknown"
                            node_props = dict(value.items())

                            record_dict[key] = f"({node_id}:{node_label} {node_props})"

                            # Add to graph data
                            if not any(v["id"] == node_id for v in graph_data["vertices"]):
                                graph_data["vertices"].append(
                                    {"id": node_id, "label": node_label, "properties": node_props}
                                )

                        # Handle relationships
                        elif (
                            hasattr(value, "type")
                            and hasattr(value, "start_node")
                            and hasattr(value, "end_node")
                        ):
                            # It's a relationship
                            rel_id = value.element_id if hasattr(value, "element_id") else value.id
                            rel_type = value.type
                            rel_props = dict(value.items())

                            start_id = (
                                value.start_node.element_id
                                if hasattr(value.start_node, "element_id")
                                else value.start_node.id
                            )
                            end_id = (
                                value.end_node.element_id
                                if hasattr(value.end_node, "element_id")
                                else value.end_node.id
                            )

                            record_dict[key] = f"[{rel_id}:{rel_type} {rel_props}]"

                            # Add nodes to graph data if not already added
                            for node, node_id in [
                                (value.start_node, start_id),
                                (value.end_node, end_id),
                            ]:
                                if not any(v["id"] == node_id for v in graph_data["vertices"]):
                                    node_label = list(node.labels)[0] if node.labels else "Unknown"
                                    node_props = dict(node.items())
                                    graph_data["vertices"].append(
                                        {
                                            "id": node_id,
                                            "label": node_label,
                                            "properties": node_props,
                                        }
                                    )

                            # Add relationship to graph data
                            if not any(e["id"] == rel_id for e in graph_data["edges"]):
                                graph_data["edges"].append(
                                    {
                                        "id": rel_id,
                                        "source": start_id,
                                        "target": end_id,
                                        "label": rel_type,
                                        "properties": rel_props,
                                    }
                                )

                        # Handle primitive values
                        else:
                            record_dict[key] = value

                    results.append(str(record_dict))

                # Save graph message
                if graph_data["vertices"] or graph_data["edges"]:
                    artifact = Artifact(
                        content_type=ContentType.GRAPH,
                        content=graph_data,
                        source_reference=SourceReference(job_id=job_id, session_id=session_id),
                        status=ArtifactStatus.FINISHED,
                        metadata=ArtifactMetadata(
                            version=1, description="It is the queried data graph."
                        ),
                    )
                    artifact_service.save_artifact(artifact=artifact)

                if not results:
                    result_str = "没有查询到数据。"
                else:
                    result_str = "\n".join(results)

                return (
                    f"Cypher查询执行成功。\n查询语句：\n{cypher_query}\n查询结果：\n{result_str}\n"
                    f"GraphJSON：\n{json.dumps(graph_data, indent=4, ensure_ascii=False)}"
                )

            except Exception as e:
                return f"Cypher查询执行失败: {str(e)}\n查询语句：\n{cypher_query}"


class VertexQuerier(Tool):
    """Tool for querying vertices in Neo4j."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.query_vertex.__name__,
            description=self.query_vertex.__doc__ or "",
            function=self.query_vertex,
        )

    def _format_value(self, value: Any) -> str:
        """Format value based on type."""
        if value is None:
            return ""

        if isinstance(value, int | float):
            return str(value)

        if isinstance(value, list | tuple):
            return str(list(value))

        return f"'{value}'"

    async def query_vertex(
        self,
        graph_db_service: GraphDbService,
        artifact_service: ArtifactService,
        session_id: str,
        job_id: str,
        vertex_type: str,
        conditions: List[Dict[str, str]],
        distinct: bool = False,
    ) -> str:
        """Query vertices with conditions. The input must have been matched with the schema of the
        graph database.

        Args:
            session_id (str): The session ID
            job_id (str): The job ID
            vertex_type (str): The vertex type to query
            conditions (List[Dict[str, str]]): List of conditions to query, which is a dict with:
                - field (str): Field name to query, should be a property of the vertex
                - operator(str): Cypher operator, valid values include:
                    General operators:
                    - DISTINCT: Return unique results
                    - . : Property access

                    Mathematical operators:
                    - +: Addition
                    - -: Subtraction
                    - *: Multiplication
                    - /: Division
                    - %: Modulo
                    - ^: Power

                    Comparison operators:
                    - =: Equal to
                    - <>: Not equal to
                    - <: Less than
                    - >: Greater than
                    - <=: Less than or equal to
                    - >=: Greater than or equal to
                    - IS NULL: Check if value is null
                    - IS NOT NULL: Check if value is not null

                    String-specific operators:
                    - STARTS WITH: String starts with
                    - ENDS WITH: String ends with
                    - CONTAINS: String contains
                    - REGEXP: Regular expression match

                    Boolean operators:
                    - AND: Logical AND
                    - OR: Logical OR
                    - XOR: Logical XOR
                    - NOT: Logical NOT

                    List operators:
                    - + : List concatenation
                    - IN: Check element existence in list
                    - []: List indexing
                - value (str, optional): Value to compare against. Required for all operators except
                    IS NULL/IS NOT NULL
            distinct (bool): Whether to return distinct results

        Returns:
            str: Query results

        Examples:
            >>> conditions = [
            ...     {"field": "name", "operator": "CONTAINS", "value": "Tech"},
            ...     {"field": "age", "operator": ">", "value": "25"},
            ...     {"field": "status", "operator": "IN", "value": ["active", "pending"]},
            ...     {"field": "description", "operator": "IS NOT NULL"}
            ... ]
            >>> result = await querier.query_vertex("session_id_xxx", "job_id_xxx", "Person", conditions, True)
        """  # noqa: E501
        where_parts = []
        for condition in conditions:
            field = condition["field"]
            operator = condition["operator"]
            value = condition.get("value")

            if operator in ("IS NULL", "IS NOT NULL"):
                where_parts.append(f"n.{field} {operator}")
            else:
                formatted_value = self._format_value(value)
                where_parts.append(f"n.{field} {operator} {formatted_value}")

        where_clause = " AND ".join(where_parts)
        distinct_keyword = "DISTINCT " if distinct else ""

        query = f"""
MATCH (n:{vertex_type})
WHERE {where_clause}
RETURN {distinct_keyword}n
        """

        store = graph_db_service.get_default_graph_db()
        results = []
        # 初始化 graph data，用于自动拼接 Graph JSON
        graph_data: Dict[str, Any] = {
            "vertices": [],
            "edges": [],  # 当前查询仅返回节点，所以 edges 为空
        }

        with store.conn.session() as session:
            result = session.run(query)

            # handle and format the results
            for record in result:
                node = record.get("n")
                if node:
                    # get properties of the vertex
                    props = dict(node.items())
                    # 使用 element_id 获取 Neo4j 4.0+ 节点ID
                    node_id = node.element_id if hasattr(node, "element_id") else node.id
                    # 构造用于返回的字符串，供文本展示使用
                    node_str = f"({node_id}:{vertex_type} {props})"
                    results.append(node_str)

                    # 构建 Graph JSON 中的 vertex 对象结构
                    vertex_obj = {"id": node_id, "label": vertex_type, "properties": props}
                    graph_data["vertices"].append(vertex_obj)

        if not results:
            result_str = "没有查询到符合条件的节点。"
        else:
            result_str = "\n".join(results)

        # 将 Graph JSON 添加到消息服务中
        if graph_data["vertices"] or graph_data["edges"]:
            artifact = Artifact(
                content_type=ContentType.GRAPH,
                content=graph_data,
                source_reference=SourceReference(job_id=job_id, session_id=session_id),
                status=ArtifactStatus.FINISHED,
                metadata=ArtifactMetadata(version=1, description="It is the queried data graph."),
            )
            artifact_service.save_artifact(artifact=artifact)

        return (
            f"查询图数据库成功。\n查询语句：\n{query}\n查询结果：\n{result_str}\n"
            f"GraphJSON：\n{json.dumps(graph_data, indent=4, ensure_ascii=False)}"
        )
