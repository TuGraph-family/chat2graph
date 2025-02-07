import json
from typing import Dict, List, Optional
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

# operation 1: Algorithms Intention Analysis
ALGORITHMS_INTENTION_ANALYSIS_PROFILE = """
你是一个专业的算法意图分析专家。你擅长理解用户的需求，并根据需求找到图数据库中支持的算法。
你需要根据用户的需求找到合适的算法，为后续的算法执行做好准备准备。
注意，你不需要执行算法，也不能询问用户更多的信息。
"""

ALGORITHMS_INTENTION_ANALYSIS_INSTRUCTION = """
1.算法需求分析
- 分析需求和具体的诉求
- 确定需要执行的算法和相关的要求
"""

ALGORITHMS_INTENTION_ANALYSIS_OUTPUT_SCHEMA = """
{
    "algorithms_supported_by_db": ["图数据库支持的算法列表，算法的名字（（名称和数据库中支持的算法名称保持一致）"],
    "selected_algorithms": [
        {
            "analysis":"算法的要求",
            "algorithm_name":"算法的名称（名称和数据库中支持的算法名称保持一致）",
            "call_objective":"调用该算法的目的"
        },
    ]
}
"""  # noqa: E501

# operation 2: Algorithms Execute
ALGORITHMS_EXECUTE_PROFILE = """
你是一个专业的图算法执行专家。你的工作是根据算法需求执行相应的图算法，并返回结果。
注意，你不能够询问用户更多的信息。
"""

ALGORITHMS_EXECUTE_INSTRUCTION = """
基于验证过的算法、算法参数，按要求完成算法执行任务：

1.运行算法
- 验证算法的可执行性（包括图数据库中是否支持该算法）
- 按照算法的输入
"""

ALGORITHMS_EXECUTE_OUTPUT_SCHEMA = """
{
    "called_algorithms": "调用的算法和参数",
    "status": "算法执行的状态",
    "algorithms_result": "算法执行的结果。如果失败，返回失败原因"
}
"""


class AlgorithmsGetter(Tool):
    """Tool to get all algorithms from the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_algorithms.__name__,
            description=self.get_algorithms.__doc__ or "",
            function=self.get_algorithms,
        )

    async def get_algorithms(self) -> str:
        """Retrieve all algorithm plugins of a specified type and version supported by the graph
        database.

        This function queries the database to fetch all algorithm plugins of type 'CPP' and version
        'v1' or 'v2', and returns their description information as a JSON formatted string.

        Returns:
            str: A JSON string containing the description information of all matching algorithm
            plugins.
        """
        plugins: List[Dict[str, str]] = []
        query_v1 = "CALL db.plugin.listPlugin('CPP','v1')"
        query_v2 = "CALL db.plugin.listPlugin('CPP','v2')"
        db = get_tugraph()
        records_1 = db.conn.run(query=query_v1)
        records_2 = db.conn.run(query=query_v2)
        for record in records_1:
            plugin_str = str(record["plugin_description"])
            plugin_json = json.loads(plugin_str)
            plugins.append(
                {
                    "algorithm_name": plugin_json["name"],
                    "algorithm_description": plugin_json["description"],
                }
            )
        for record in records_2:
            plugin_str = str(record["plugin_description"])
            plugin_json = json.loads(plugin_str)
            plugins.append(
                {
                    "algorithm_name": plugin_json["name"],
                    "algorithm_description": plugin_json["description"],
                }
            )

        return json.dumps(plugins, indent=4)


class AlgorithmsExecutor(Tool):
    """Tool to execute algorithms on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_algorithms.__name__,
            description=self.execute_algorithms.__doc__ or "",
            function=self.execute_algorithms,
        )

    async def execute_algorithms(self, algorithms_name: str) -> str:
        """Execute the specified algorithm on the graph database.

        This function calls the specified algorithm plugin on the graph database and returns the
        result.

        Args:
            algorithms_name (str): The name of the algorithm to execute. Pay attention to the format
            of the algorithm name.

        Returns:
            str: The result of the algorithm execution.
        """
        query = f"""CALL db.plugin.callPlugin(
            'CPP', 
            '{algorithms_name}', 
            '{{"num_iterations": 100}}', 
            10000.0, 
            false
        )"""

        db = get_tugraph()
        result = db.conn.run(query=query)

        return str(result)


def get_algorithms_intention_analysis_operator():
    """Get the operator for algorithms intention analysis."""
    analysis_toolkit = Toolkit()
    content_understanding_action = Action(
        id="algorithms_intention_analysis.content_understanding",
        name="内容理解",
        description="理解和分析用户的需求",
    )
    algorithms_intention_identification_action = Action(
        id="query_intention_analysis.query_intention_identification",
        name="核心算法意图识别",
        description="识别并理解用户需求中的算法要求，调用相关工具函数查找图数据库中支持的算法，然后基于此确定算法的名称和要求",
    )
    algorithms_getter = AlgorithmsGetter(id="algorithms_getter_tool")

    analysis_toolkit.add_action(
        action=content_understanding_action,
        next_actions=[(algorithms_intention_identification_action, 1)],
        prev_actions=[],
    )
    analysis_toolkit.add_action(
        action=algorithms_intention_identification_action,
        next_actions=[],
        prev_actions=[(content_understanding_action, 1)],
    )
    analysis_toolkit.add_tool(
        tool=algorithms_getter,
        connected_actions=[(algorithms_intention_identification_action, 1)],
    )

    operator_config = OperatorConfig(
        id="algorithms_intention_analysis_operator",
        instruction=ALGORITHMS_INTENTION_ANALYSIS_PROFILE
        + ALGORITHMS_INTENTION_ANALYSIS_INSTRUCTION,
        output_schema=ALGORITHMS_INTENTION_ANALYSIS_OUTPUT_SCHEMA,
        actions=[
            content_understanding_action,
            algorithms_intention_identification_action,
        ],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=analysis_toolkit),
    )

    return operator


def get_algorithms_execute_operator():
    """Get the operator for algorithms execution."""
    analysis_toolkit = Toolkit()
    algorithms_validation_action = Action(
        id="algorithms_execute.algorithms_validation_action",
        name="算法执行验证",
        description="确认当前图数据库中的算法是否支持相关的需求",
    )
    algorithms_execution_aciton = Action(
        id="algorithms_execute.algorithms_execution_aciton",
        name="执行查询",
        description="在对应图上执行查询语句返回结果",
    )
    algorithms_getter = AlgorithmsGetter(id="algorithms_getter_tool")
    algorithms_excute = AlgorithmsExecutor(id="algorithms_excute_tool")

    analysis_toolkit.add_action(
        action=algorithms_validation_action,
        next_actions=[(algorithms_execution_aciton, 1)],
        prev_actions=[],
    )
    analysis_toolkit.add_action(
        action=algorithms_execution_aciton,
        next_actions=[],
        prev_actions=[(algorithms_validation_action, 1)],
    )
    analysis_toolkit.add_tool(
        tool=algorithms_getter, connected_actions=[(algorithms_validation_action, 1)]
    )
    analysis_toolkit.add_tool(
        tool=algorithms_excute, connected_actions=[(algorithms_execution_aciton, 1)]
    )

    operator_config = OperatorConfig(
        id="algorithms_execute_operator",
        instruction=ALGORITHMS_EXECUTE_PROFILE + ALGORITHMS_EXECUTE_INSTRUCTION,
        output_schema=ALGORITHMS_EXECUTE_OUTPUT_SCHEMA,
        actions=[algorithms_validation_action, algorithms_execution_aciton],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=analysis_toolkit),
    )
    return operator


def get_graph_analysis_workflow():
    """Get the workflow for graph modeling and assemble the operators."""
    algorithms_intention_analysis_operator = get_algorithms_intention_analysis_operator()
    algorithms_execute_operator = get_algorithms_execute_operator()

    workflow = DbgptWorkflow()
    workflow.add_operator(
        operator=algorithms_intention_analysis_operator,
        previous_ops=[],
        next_ops=[algorithms_execute_operator],
    )
    workflow.add_operator(
        operator=algorithms_execute_operator,
        previous_ops=[algorithms_intention_analysis_operator],
        next_ops=[],
    )

    return workflow


def get_graph_analysis_expert_config(reasoner: Optional[Reasoner] = None) -> AgentConfig:
    """Get the expert configuration for graph analysis."""

    expert_config = AgentConfig(
        profile=Profile(name="Graph Analysis Expert", description=ALGORITHMS_EXECUTE_PROFILE),
        reasoner=reasoner or DualModelReasoner(),
        workflow=get_graph_analysis_workflow(),
    )

    return expert_config
