import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.service.graph_db_service import GraphDbService
from app.core.toolkit.tool import Tool

QUERY_GRAMMER = """
===== 图vertex查询语法书 =====
简单例子：
MATCH (p:种类 {筛选条件}) RETURN p
MATCH (p:种类), (q:种类) WHERE p,q的条件 RETURN p,q
=====
"""


class SchemaGetter(Tool):
    """Tool for getting the schema of the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_schema.__name__,
            description=self.get_schema.__doc__ or "",
            function=self.get_schema,
        )

    async def get_schema(self, graph_db_service: GraphDbService) -> str:
        """Get the schema of the graph database.

        Args:
            None args required

        Returns:
            str: The schema of the graph database in string format

        Example:
            schema_str = get_schema()
        """
        query = "CALL dbms.graph.getGraphSchema()"
        store = graph_db_service.get_default_graph_db()
        schema = store.conn.run(query=query)

        return json.dumps(json.loads(schema[0][0])["schema"], indent=4, ensure_ascii=False)


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
    """Tool for querying vertices in TuGraph."""

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
        vertex_type: str,
        conditions: List[Dict[str, str]],
        distinct: bool = False,
    ) -> str:
        """Query vertices with conditions. The input must have been matched with the schema of the
        graph database.

        Args:
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
            >>> result = await querier.query_vertex("Person", conditions, True)
        """
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
        result = "\n".join([str(record.get("n", "")) for record in store.conn.run(query=query)])
        return f"查询图数据库成功。\n查询语句：\n{query}：\n查询结果：\n{result}"
