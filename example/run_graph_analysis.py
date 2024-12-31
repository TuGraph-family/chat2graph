import asyncio
import json
from typing import Optional

from dbgpt.storage.graph_store.tugraph_store import TuGraphStore, TuGraphStoreConfig

from app.agent.job import Job
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.workflow.operator.operator import Operator, OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit, ToolkitService


# global function to get tugraph store
def get_tugraph(
    config: Optional[TuGraphStoreConfig] = None,
) -> TuGraphStore:
    """initialize tugraph store with configuration.

    args:
        config: optional tugraph store configuration

    returns:
        initialized tugraph store instance
    """
    try:
        if not config:
            config = TuGraphStoreConfig(
                name="default_graph",
                host="127.0.0.1",
                port=7687,
                username="admin",
                password="73@TuGraph",
            )

        # initialize store
        store = TuGraphStore(config)

        # ensure graph exists
        print(f"[log] get graph: {config.name}")
        store.conn.create_graph(config.name)

        return store

    except Exception as e:
        print(f"failed to initialize tugraph: {str(e)}")
        raise


# operation 1: Algorithms Intention Analysis
ALGORITHMS_INTENTION_ANALYSIS_PROFILE = """
你是一个专业的算法意图分析专家。你的工作是，理解用户的需求，给出一些算法建议，然后为后续的执行算法语句做好准备工作。
你需要识别用户所说内容为图算法的需求。你的任务是分析用户需求，并给出适合用户需求的算法，为后续的执行算法做准备。
"""

ALGORITHMS_INTENTION_ANALYSIS_INSTRUCTION = """
请理解用户所说的需求，按要求完成任务：

1.算法需求分析
- 识别用户的需求
- 理解用户对于算法的具体诉求
- 确定用户描述的算法需求内容是完整的
"""

ALGORITHMS_INTENTION_ANALYSIS_OUTPUT_SCHEMA = """
{
    "algorithms": [
        {
            "analysis":"算法的要求",
            "algorithms_name":"算法的名称",
        },
    ]
}
"""
# operation 2: Algorithms Validation
ALGORITHMS_VALIDATION_PROFILE = """
你是一个专业的算法检测专家。你的工作是校验用户的算法需求和实际图数据库中的可执行算法是否匹配。
"""

ALGORITHMS_VALIDATION_INSTRUCTION = """
基于算法需求分析的结果，按要求完成算法检测任务：

1.检测算法是否存在
- 验证当前图数据库中是否存在相应的算法
2.检测算法的必要参数
- 检测用户是否已提供算法的必要参数
"""

ALGORITHMS_VALIDATION_OUTPUT_SCHEMA = """
{
    "status": "算法检测状态：是否通过验证",
    "supplement": "需要补充的缺少的或无法匹配的信息"
    "algorithms_name":"通过验证的算法名称",
    "algorithms_parameters": "通过验证的算法参数"
}
"""

# operation 3: Algorithms Execute
ALGORITHMS_EXECUTE_PROFILE = """
你是一个专业的图算法执行专家。你的工作是根据用户的算法需求执行相应的图算法，并返回结果。
"""

ALGORITHMS_EXECUTE_INSTRUCTION = """
基于验证过的算法、算法参数，按要求完成算法执行任务：

1.运行算法
- 按照算法的输入
"""

ALGORITHMS_EXECUTE_OUTPUT_SCHEMA = """
{
    "call_algorithms": "算法的执行命令",
    "algorithms_result": "算法执行的结果"
}
"""


class AlgorithmsGetter(Tool):
    """Tool to get all algorithms from the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id,
            name=self.get_algorithms.__name__,
            description=self.get_algorithms.__doc__,
            function=self.get_algorithms,
        )

    async def get_algorithms(self) -> str:
        """Retrieve all algorithm plugins of a specified type and version supported by the graph database.

        This function queries the database to fetch all algorithm plugins of type 'CPP' and version 'v1', and returns their description information as a JSON formatted string.

        Returns:
            str: A JSON string containing the description information of all matching algorithm plugins.
        """
        plugins = []
        query = "CALL db.plugin.listPlugin('CPP','v1')"
        db = get_tugraph()
        result = db.conn.run(query=query)
        for item in result:
            plugins.append(item["plugin_description"])
        return json.dumps(plugins)


class AlgorithmsExecute(Tool):
    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id,
            name=self.excute_algorithms.__name__,
            description=self.excute_algorithms.__doc__,
            function=self.excute_algorithms,
        )

    async def excute_algorithms(self, algorithms_name: str):
        query = f"CALL db.plugin.callPlugin('CPP','{algorithms_name}')"
        db = get_tugraph()
        result = db.conn.run(query=query)

        return result


def get_algorithms_intention_analysis_operator():
    analysis_toolkit = Toolkit()
    content_understanding_action = Action(
        id="algorithms_intention_analysis.content_understanding",
        name="内容理解",
        description="理解用户所说的所有内容",
    )
    algorithms_intention_identification_action = Action(
        id="query_intention_analysis.query_intention_identification",
        name="核心算法意图识别",
        description="识别并理解用户需求中的算法要求，确定算法的名称和要求",
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


def get_algorithms_validation_operator():
    analysis_toolkit = Toolkit()
    algorithms_validation_action = Action(
        id="algorithms_validation.algorithms_validation_action",
        name="算法执行验证",
        description="查询当前图数据库中的算法是否和用户的算法需求匹配",
    )
    algorithms_parameters_validation_action = Action(
        id="algorithms_validation.condition_validation_action",
        name="算法参数验证",
        description="验证算法的参数和需求匹配",
    )
    algorithms_getter = AlgorithmsGetter(id="algorithms_getter_tool")

    analysis_toolkit.add_action(
        action=algorithms_validation_action,
        next_actions=[(algorithms_parameters_validation_action, 1)],
        prev_actions=[],
    )
    analysis_toolkit.add_action(
        action=algorithms_parameters_validation_action,
        next_actions=[],
        prev_actions=[(algorithms_validation_action, 1)],
    )
    analysis_toolkit.add_tool(
        tool=algorithms_getter, connected_actions=[(algorithms_validation_action, 1)]
    )

    operator_config = OperatorConfig(
        id="algorithms_validation_operator",
        instruction=ALGORITHMS_VALIDATION_PROFILE + ALGORITHMS_VALIDATION_INSTRUCTION,
        output_schema=ALGORITHMS_VALIDATION_OUTPUT_SCHEMA,
        actions=[algorithms_validation_action, algorithms_parameters_validation_action],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=analysis_toolkit),
    )
    return operator


def get_algorithms_execute_operator():
    analysis_toolkit = Toolkit()
    algorithms_execution_aciton = Action(
        id="algorithms_execute.algorithms_execution_aciton",
        name="执行查询",
        description="在对应图上执行查询语句返回结果",
    )
    analysis_toolkit.add_action(
        action=algorithms_execution_aciton,
        next_actions=[],
        prev_actions=[],
    )
    algorithms_excute = AlgorithmsExecute(id="algorithms_excute_tool")
    analysis_toolkit.add_tool(
        tool=algorithms_excute, connected_actions=[(algorithms_execution_aciton, 1)]
    )
    operator_config = OperatorConfig(
        id="algorithms_execute_operator",
        instruction=ALGORITHMS_EXECUTE_PROFILE + ALGORITHMS_EXECUTE_INSTRUCTION,
        output_schema=ALGORITHMS_EXECUTE_OUTPUT_SCHEMA,
        actions=[algorithms_execution_aciton],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=analysis_toolkit),
    )
    return operator


def get_graph_analysis_workflow():
    """Get the workflow for graph modeling and assemble the operators."""
    algorithms_intention_analysis_operator = (
        get_algorithms_intention_analysis_operator()
    )
    algorithms_validation_operator = get_algorithms_validation_operator()
    algorithms_execute_operator = get_algorithms_execute_operator()

    workflow = DbgptWorkflow()
    workflow.add_operator(
        operator=algorithms_intention_analysis_operator,
        previous_ops=[],
        next_ops=[algorithms_validation_operator],
    )
    workflow.add_operator(
        operator=algorithms_validation_operator,
        previous_ops=[algorithms_intention_analysis_operator],
        next_ops=[algorithms_execute_operator],
    )

    workflow.add_operator(
        operator=algorithms_execute_operator,
        previous_ops=[algorithms_validation_operator],
        next_ops=[],
    )

    return workflow


async def main():
    """Main function"""
    workflow = get_graph_analysis_workflow()

    job = Job(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="目前我们的问题的背景是，理解用户输入的需求，识别出用户想要执行的图算法，并匹配上图数据库已加载的图算法，最后执行该图算法并返回结果。"
        "基于节点之间的关系结构，对当前图谱的节点进行排序，并找到最重要的节点",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
