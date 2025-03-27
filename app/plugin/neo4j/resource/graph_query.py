from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.toolkit.tool import Tool
from app.plugin.neo4j.neo4j_store import get_neo4j
from app.plugin.neo4j.resource.read_doc import SchemaManager

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

    async def get_schema(self) -> str:
        """Get the schema of the graph database.

        Args:
            None args required

        Returns:
            str: The schema of the graph database in string format
        """
        schema = await SchemaManager.read_schema()

        result = "# Neo4j Graph Schema\n\n"

        # vertices information
        result += "## Node Labels\n\n"
        for label, info in schema["nodes"].items():
            result += f"### {label}\n"
            result += f"- Primary Key: `{info['primary_key']}`\n"
            result += "- Properties:\n"
            for prop in info["properties"]:
                index_info = ""
                if prop["has_index"]:
                    index_info = f" (Indexed: {prop['index_name']})"
                else:
                    index_info = " (Indexed: not indexed)"
                result += f"  - `{prop['name']}` ({prop['type']}){index_info}\n"
            result += "\n"

        # edges information
        result += "## Relationship Types\n\n"
        for label, info in schema["relationships"].items():
            result += f"### {label}\n"
            result += f"- Primary Key: `{info['primary_key']}`\n"
            result += "- Properties:\n"
            for prop in info["properties"]:
                index_info = ""
                if prop["has_index"]:
                    index_info = f" (Indexed: {prop['index_name']})"
                result += f"  - `{prop['name']}` ({prop['type']}){index_info}\n"
            result += "\n"

        return result


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
        self, vertex_type: str, conditions: List[Dict[str, str]], distinct: bool = False
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

        store = get_neo4j()
        results = []

        with store.conn.session() as session:
            result = session.run(query)

            # handle and format the results
            for record in result:
                node = record.get("n")
                if node:
                    # get properties of the vertex
                    props = dict(node.items())
                    # use element_id to get node id in Neo4j 4.0+
                    node_id = node.element_id if hasattr(node, "element_id") else node.id
                    node_str = f"({node_id}:{vertex_type} {props})"
                    results.append(node_str)

        result_str = "\n".join(results)
        return f"查询图数据库成功。\n查询语句：\n{query}：\n查询结果：\n{result_str}"
