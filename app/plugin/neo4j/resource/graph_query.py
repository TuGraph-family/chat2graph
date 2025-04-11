import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.model.message import GraphMessage
from app.core.service.graph_db_service import GraphDbService
from app.core.service.message_service import MessageService
from app.core.toolkit.tool import Tool
from app.plugin.neo4j.resource.doc import QUERY_GRAMMER


class GrammerReader(Tool):
    """Tool for reading the graph query language grammar."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.read_grammer.__name__,
            description=self.read_grammer.__doc__ or "",
            function=self.read_grammer,
        )

    async def read_grammer(self) -> str:
        """Read the graph query language grammar book fot querying vertices.

        Args:
            None args required, use {}

        Returns:
            str: The graph query language grammar

        Example:
            grammer = read_grammer()
        """
        return QUERY_GRAMMER


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
        message_service: MessageService,
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
        graph_message = GraphMessage(
            payload=graph_data,
            job_id=job_id,
            session_id=session_id,
        )
        message_service.save_message(message=graph_message)

        return (
            f"查询图数据库成功。\n查询语句：\n{query}\n查询结果：\n{result_str}\n"
            f"GraphJSON：\n{json.dumps(graph_data, indent=4, ensure_ascii=False)}"
        )
