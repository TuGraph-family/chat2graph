import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.agent.agent import AgentConfig, Profile
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator, OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.plugin.tugraph.tugraph_store import get_tugraph
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit, ToolkitService

QUERY_GRAMMER = """
===== 图vertex查询语法书 =====
简单例子：
MATCH (p:种类 {筛选条件}) RETURN p
MATCH (p:种类), (q:种类) WHERE p,q的条件 RETURN p,q
=====
"""

# operation 1: Query Intention Analysis
QUERY_INSTRUCTION_AYNALYSIS_PROFILE = """
你是一位专业的查询意图识别专家。你的工作是，理解给定的输入，给出一些结论，然后为后续的写查询语句做好准备工作。
你需要识别图查询的诉求，并校验查询的节点内容和对应的图模型是否匹配。注意你的任务不是将输入进行查询语句的转换，而是识别出存在着单点查询的诉求。
如通过主键查询节点需要有指定的节点类型和明确的主键，如通过节点的普通属性查询需要指定节点类型、正确的属性筛选条件，并在模型上有对应的属性索引
"""

QUERY_INTENTION_ANALYSIS_INSTRUCTION = """
请理解提供的内容和上下文，按要求完成任务：

1. 内容分析
- 理解内容中的单点查询的诉求
- 确定描述的单点查询内容是完整的
- 识别出有多个节点查询的情况

2. 查询检测
- 验证查询的节点种类是否和对应的模型相匹配
- 验证查询的条件是否和对应模型相匹配
- 如果有不匹配的情况，需要补充缺少的内容

3. 避免错误
- 请不要将查询的内容转换为查询语句，也不要执行查询语句，这不是你的任务
"""

QUERY_INTENTION_ANALYSIS_OUTPUT_SCHEMA = """
{
    "analysis": "内容中查询要求",
    "object_node_type": "单点查询点的种类",
    "query_condition":"查询的条件"
    "supplement": "需要补充的缺少的或无法匹配的信息"
}
"""

# operation 2: Query Design
QUERY_DESIGN_PROFILE = """
你是一位专业的图查询语言设计专家。你的工作是根据查询要求使用对应的图查询语言语法设计出对应的图查询语言，并执行该查询语句。
如节点查询最常用的语法为 MATCH, WHERE, RETURN 等。你不具备写 Cypher 的能力，你只能调用工具来帮助你达到相关的目的。
"""  # noqa: E501

QUERY_DESIGN_INSTRUCTION = """
基于经验证过的图模型、查询节点和查询条件，按要求完成图查询语言设计的任务：

1. 语法学习与工具调用
- 按查询要求在图查询语法文档中匹配学习对应语法，会正确调用图数据库的工具函数。
- 了解图查询语法的基本结构和语法规则，如果得到调用错误信息，需要及时调整查询语句。

2. 查询结果交付
- 在最后，根据查询意图，交付查询的结果。
"""

QUERY_DESIGN_OUTPUT_SCHEMA = """
{
    "query": "需要的图查询指令",
    "query_result": "查询语言在对应图上的查询结果"
}
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

        Example:
            schema_str = get_schema()
        """
        query = "CALL dbms.graph.getGraphSchema()"
        store = get_tugraph()
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

        store = get_tugraph()
        result = "\n".join([str(record.get("n", "")) for record in store.conn.run(query=query)])
        return f"查询图数据库成功。\n查询语句：\n{query}：\n查询结果：\n{result}"


def get_query_intention_analysis_operator():
    """Get the operator for query intention analysis."""
    query_intention_identification_action = Action(
        id="query_intention_analysis.query_intention_identification",
        name="核心查询意图识别",
        description="识别并理解提供的查询要求，提取出查询针对的图模型名称、查询点的种类和查询条件",
    )
    node_type_validation_action = Action(
        id="schema_check.node_type_validation_action",
        name="节点种类验证",
        description="读取图数据现有的 schema，以帮助检查节点类型是否和对应的模型匹配",
    )
    condition_validation_action = Action(
        id="schema_check.condition_validation_action",
        name="查询条件验证",
        description="读取图数据现有的 schema，以帮助检查条件是否和对应的模型匹配",
    )
    supplement_aciton = Action(
        id="schema_check.supplement_aciton",
        name="补充缺少内容",
        description="如查询条件/节点类型缺少或不匹配，则需要经过自己的思考和推理，补充缺少的查询内容",
    )
    schema_getter = SchemaGetter("schema_getter_tool")

    query_intention_query_design_toolkit = Toolkit()

    query_intention_query_design_toolkit.add_action(
        action=query_intention_identification_action,
        next_actions=[(node_type_validation_action, 1)],
        prev_actions=[],
    )
    query_intention_query_design_toolkit.add_action(
        action=node_type_validation_action,
        next_actions=[(condition_validation_action, 1)],
        prev_actions=[(query_intention_identification_action, 1)],
    )
    query_intention_query_design_toolkit.add_action(
        action=condition_validation_action,
        next_actions=[(supplement_aciton, 1)],
        prev_actions=[(node_type_validation_action, 1)],
    )
    query_intention_query_design_toolkit.add_action(
        action=supplement_aciton,
        next_actions=[],
        prev_actions=[(condition_validation_action, 1)],
    )
    query_intention_query_design_toolkit.add_tool(
        tool=schema_getter,
        connected_actions=[
            (node_type_validation_action, 1),
            (condition_validation_action, 1),
        ],
    )

    operator_config = OperatorConfig(
        id="query_intention_analysis_operator",
        instruction=QUERY_INSTRUCTION_AYNALYSIS_PROFILE + QUERY_INTENTION_ANALYSIS_INSTRUCTION,
        output_schema=QUERY_INTENTION_ANALYSIS_OUTPUT_SCHEMA,
        actions=[
            query_intention_identification_action,
            node_type_validation_action,
            condition_validation_action,
            supplement_aciton,
        ],
    )

    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=query_intention_query_design_toolkit),
    )

    return operator


def get_query_design_operator():
    """Get the operator for query design."""
    query_design_toolkit = Toolkit()

    grammar_study_action = Action(
        id="query_design.grammar_study_action",
        name="语法学习",
        description="按查询要求在图查询语法文档中学习对应语法",
    )
    query_execution_aciton = Action(
        id="query_design.query_execution_aciton",
        name="执行查询",
        description=(
            "根据图查询语法、图现有 schema 和查询要求，调用图数据库工具函数，"
            "在对应图上执行查询语句得到结果"
        ),
    )
    grammer_reader = GrammerReader("grammer_reader_tool")
    schema_getter = SchemaGetter("schema_checker_tool_v2")
    vertex_querier = VertexQuerier("vertex_querier_tool")

    query_design_toolkit.add_action(
        action=grammar_study_action,
        next_actions=[(query_execution_aciton, 1)],
        prev_actions=[],
    )
    query_design_toolkit.add_action(
        action=query_execution_aciton,
        next_actions=[],
        prev_actions=[(grammar_study_action, 1)],
    )
    query_design_toolkit.add_tool(
        tool=grammer_reader,
        connected_actions=[(grammar_study_action, 1)],
    )
    query_design_toolkit.add_tool(
        tool=schema_getter,
        connected_actions=[(query_execution_aciton, 1)],
    )
    query_design_toolkit.add_tool(
        tool=vertex_querier,
        connected_actions=[(query_execution_aciton, 1)],
    )

    operator_config = OperatorConfig(
        id="analysis_operator",
        instruction=QUERY_DESIGN_PROFILE + QUERY_DESIGN_INSTRUCTION,
        output_schema=QUERY_DESIGN_OUTPUT_SCHEMA,
        actions=[grammar_study_action, query_execution_aciton],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=query_design_toolkit),
    )

    return operator


def get_graph_query_workflow():
    """Get the workflow for graph modeling and assemble the operators."""
    qery_intention_analysis_operator = get_query_intention_analysis_operator()
    query_design_operator = get_query_design_operator()

    workflow = DbgptWorkflow()
    workflow.add_operator(
        operator=qery_intention_analysis_operator,
        previous_ops=[],
        next_ops=[query_design_operator],
    )
    workflow.add_operator(
        operator=query_design_operator,
        previous_ops=[qery_intention_analysis_operator],
        next_ops=[],
    )

    return workflow


def get_graph_query_expert_config(reasoner: Optional[Reasoner] = None) -> AgentConfig:
    """Get the expert configuration for graph modeling."""

    expert_config = AgentConfig(
        profile=Profile(name="Graph Query Expert", description=QUERY_DESIGN_PROFILE),
        reasoner=reasoner or DualModelReasoner(),
        workflow=get_graph_query_workflow(),
    )

    return expert_config
