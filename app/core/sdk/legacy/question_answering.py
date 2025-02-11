from typing import List, Optional, Tuple
from uuid import uuid4

from app.core.agent.agent import AgentConfig, Profile
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator import Operator, OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.toolkit import Toolkit, ToolkitService

# operation 1: Document Retrieving
DOC_RETRIEVING_PROFILE = """
你是一位专业的文档检索专家。你的工作是，从知识库以及互联网两个信息来源检索与问题相关的文档，
仔细阅读检索得到的文档材料，分别总结每一份文档，为后续回答用户问题作准备。
你阅读的文档未必与用户的问题直接相关，但是你仍然需要进行清晰全面的总结。
你的任务是检索并总结文档，为后续推理得到最终的答案做铺垫。
"""

DOC_RETRIEVING_INSTRUCTION = """
请认真理解给定的问题，同时，按要求完成任务：

1.文档检索
- 通过知识库检索得到与问题相关的文档
- 通过互联网检索得到与问题相关的网页
2. 文档整理
- 将知识库中检索得到各个文档分别总结为一段内容
- 将互联网中检索得到各个网页内容分别总结为一段内容
"""

DOC_RETRIEVING_OUTPUT_SCHEMA = """
{
    "original_question": "输入的原始提问",
    "knowledge_base_result": ["知识库中", “检索得到的", "相关内容", "总结"],
    "knowledge_base_references": ["知识库中", “检索得到的", "相关内容", "对应的", "章节编号"],
    "internet_result": ["互联网", "搜索引擎中", "检索得到的", "相关内容", "总结"]
    "internet_references": ["互联网", "搜索引擎中", "检索得到的", "相关内容", "对应的", "网址"]
}
"""

# operation 2: Document Summarizing
DOC_SUMMARIZING_PROFILE = """
你是一位文档总结专家,擅长总结归纳不同来源的文档。你需要根据用户的问题，总结归纳出用户需要的答案。
"""

DOC_SUMMARIZING_INSTRUCTION = """
基于检索得到的文档内容,完成以下文档总结任务:

1. 分别总结不同来源的文档内容
- 总结从知识库中检索得到问题相关内容
- 总结从互联网搜索引擎中检索得到问题相关内容

2. 归纳不同来源的总结结果
- 分析不同来源的文档总结的相同点与不同点
- 归纳得出一份更完整的总结内容

3. 答案生成
- 分析问题的实际意图
- 根据问题与归纳总结的文档内容，生成一份回答
- 提供回答中涉及的原文出处，给出一个List，其中包含markdown格式的原文链接
"""

DOC_SUMMARIZING_OUTPUT_SCHEMA = """
{
    "anwser": "针对用户问题的最终回答",
    "references": ["回答生成", "过程中", "参考的", "文档原文的", "markdown格式", "链接"]
}
"""

TUGRAPH_DOC = [
    """
===== TuGraph Cypher 语法书 =====

createVertexLabelByJson 命令用于创建顶点标签，基本语法：

```
CALL db.createVertexLabelByJson('{
    "label": "标签名",
    "primary": "主键字段名",
    "type": "VERTEX",
    "properties": [
        {
            "name": "字段名",
            "type": "字段类型",
            "optional": True/False,
            "index": True/False,
        }
        // ... 更多属性
    ]
}');
```

createEdgeLabelByJson 命令用于创建边标签，基本语法：

```
CALL db.createEdgeLabelByJson('{
    "label": "边标签名",
    "type": "EDGE",
    "properties": [
        {
            "name": "type",
            "type": "STRING",
            "optional": False,
        },
        // ... 更多属性
    ],
    "constraints": [
        ["源实体标签名", "目标实体标签名"],
    ]
}');
```

关键参数说明：

1. 顶点标签必填字段：
   - label: 节点标签名
   - primary: 主键字段名
   - type: 必须为 "VERTEX"
   - properties: 至少包含主键属性

2. 边标签必填字段：
   - label: 边标签名
   - type: 必须为 "EDGE"
   - properties: 至少包含主键属性

属性定义规则：
- name: 属性名
- type: 属性类型（见下方支持的数据类型）
- optional: 是否可选（True/False）
- index: 是否建立索引（可选参数）(字符串字段如果需要查询，建议设置 index: True)

支持的数据类型：
- 整数类型：INT8, INT16, INT32, INT64
- 浮点类型：FLOAT, DOUBLE
- 其他类型：STRING, BOOL, DATE, DATETIME

重要注意事项：

1. 格式要求：
   - JSON 必须用单引号包裹
   - 所有字符串值使用双引号
   - 标签名和字段名不能包含特殊字符

2. 字段规则：
   - 主键字段必须设置 optional: False

=====
""",
    """
### 1.2. 数据类型

TuGraph支持多种可用于属性的数据类型。具体支持的数据类型如下：

| **数据类型** | **最小值**          | **最大值**          | **描述**                            |
| ------------ | ------------------- | ------------------- | ----------------------------------- |
| BOOL         | false               | true                | 布尔值                              |
| INT8         | -128                | 127                 | 8位整型                          |
| INT16        | -32768              | 32767               | 16位整型                         |
| INT32        | - 2^31              | 2^31 - 1            | 32位整型                         |
| INT64        | - 2^63              | 2^63 - 1            | 64位整型                         |
| DATE         | 0000-00-00          | 9999-12-31          | "YYYY-MM-DD" 格式的日期             |
| DATETIME     | 0000-00-00 00:00:00.000000 | 9999-12-31 23:59:59.999999 | "YYYY-MM-DD HH:mm:ss[.ffffff]" 格式的日期时间 |
| FLOAT        |                     |                     | 32位浮点数                       |
| DOUBLE       |                     |                     | 64位浮点数                       |
| STRING       |                     |                     | 不定长度的字符串                    |
| BLOB         |                     |                     | 二进制数据（在输入输出时使用Base64编码） |
| POINT        |                     |                     | EWKB格式数据，表示点              |
| LINESTRING   |                     |                     | EWKB格式数据，表示线              |
| POLYGON      |                     |                     | EWKB格式数据，表示面(多边形)       |
| FLOAT_VECTOR |                     |                     | 包含32位浮点数的动态向量               |
""",  # noqa: E501
]

TUGRAPH_REF = ["TuGraph-Cpyher语法书", "TuGraph图模型说明-数据类型"]

INTERNET_DOC = [
    """
Neo4j是一款流行的图数据库，它使用Cypher查询语言来操作和查询图数据。在Python中，我们可以使用Neo4j的官方驱动程序或第三方库（如py2neo）来与数据库进行交互。然而，当我们执行某些复杂的Cypher查询时，有时会发现结果被截断或不完整显示。下面将介绍可能导致此问题的原因，并提供相应的解决方案。
1.原因分析
该问题通常是由以下原因之一引起的：
-默认限制：Neo4j驱动程序在执行Cypher查询时，默认会对结果进行限制。这个限制通常是为了避免查询结果过大导致性能问题。因此，在显示结果时，驱动程序只会显示一部分数据，而不是全部。
-结果截断：如果查询结果非常庞大，超出了驱动程序的限制，结果将被截断并丢失一部分数据。这可能会导致我们无法看到完整的结果。
2.解决方案
根据原因，下面提供几种解决方案：
-增加限制：如果您确定查询结果不会导致性能问题，可以通过设置Neo4j驱动程序的配置选项来增加默认限制。例如，对于官方驱动程序，您可以使用`session.run`方法的`max_records`参数来增加限制。但请注意，增加限制可能会影响性能，因此请根据具体情况谨慎使用。
-使用分页查询：如果查询结果仍然超出限制，您可以考虑使用分页查询来获取完整的结果。通过在Cypher查询中使用`SKIP`和`LIMIT`子句，您可以按照指定的步长逐渐获取结果集的不同部分。然后，您可以在Python中使用循环来合并所有分页结果，并显示完整的结果。
-导出到文件：如果以上方法仍无法满足您的需求，您可以将查询结果导出到文件中进行查看。Neo4j驱动程序通常提供将结果导出为CSV或其他格式的功能。您可以将结果导出为文件，然后在Python中读取和查看结果。
3.检查解决方案
根据您的需求选择合适的解决方案后，重新运行查询并检查是否成功显示完整的结果。如果结果仍然不完整，请确保您已正确设置驱动程序的配置选项或正确实现分页查询。如果您选择将结果导出到文件，请确保文件中包含完整的结果。
当在Python中使用Neo4j图数据库执行Cypher查询时，有时会遇到结果不完整显示的问题。这是由于默认限制或结果截断导致的。通过增加限制、使用分页查询或将结果导出到文件，我们可以解决这个问题，并获得完整的Cypher查询结果。根据具体需求，请选择适合您的解决方案，以便在Python中正常查看和处理Neo4j查询结果。
分享快讯到朋友圈
"""  # noqa: E501
]

INTERNET_REF = [
    "https://cloud.tencent.com/developer/news/1294500",
]


class KnowledgeBaseRetriever(Tool):
    """Tool for retrieving document content from knowledge base."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.knowledge_base_search.__name__,
            description=self.knowledge_base_search.__doc__ or "",
            function=self.knowledge_base_search,
        )

    async def knowledge_base_search(self, question: str) -> Tuple[List[str], List[str]]:
        """Retrive a list of related contents and a list of their reference name from knowledge
        base given the question.

        Args:
            question (str): The question asked by user.

        Returns:
            (List[str], List[str]): The list of related contents and the list of reference name.
        """

        return TUGRAPH_DOC, TUGRAPH_REF


class InternetRetriever(Tool):
    """Tool for retrieving webpage contents from Internet."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.internet_search.__name__,
            description=self.internet_search.__doc__ or "",
            function=self.internet_search,
        )

    async def internet_search(self, question: str) -> Tuple[List[str], List[str]]:
        """Retrive a list of related webpage contents and a list of their URL references from
        Internet given the question.

        Args:
            question (str): The question asked by user.

        Returns:
            Tuple[List[str], List[str]]: The list of related webpage contents and the list of URL
            references.
        """

        return INTERNET_DOC, INTERNET_REF


class ReferenceGenerator(Tool):
    """Tool for generating rich text references."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.reference_listing.__name__,
            description=self.reference_listing.__doc__ or "",
            function=self.reference_listing,
        )

    async def reference_listing(
        self, knowledge_base_references: List[str], internet_references: List[str]
    ) -> List[str]:
        """Return a rich text references list for better presentation given the list of references.

        Args:
            knowledge_base_references (List[str]): references from knowledge base.
            internet_references (List[str]): references from internet.

        Returns:
            str: The rich text to demonstrate all references.
        """

        reference_list: List[str] = []
        for knowledge_base_ref in knowledge_base_references:
            reference_list.append(f"[{knowledge_base_ref}]()")
        for inernet_ref in internet_references:
            reference_list.append(f"[网页链接]({inernet_ref})")

        return reference_list


def get_retrieving_operator():
    """Get the operator for document retrieving."""
    retrieving_toolkit = Toolkit()

    knowledge_base_retrieving = Action(
        id="doc_retrieving.vector_retrieving",
        name="知识库检索",
        description="调用knowledge_base_search工具，从外接知识库中检索得到问题相关的文档",
    )
    internet_retrieving = Action(
        id="doc_retrieving.internet_retrieving",
        name="互联网检索",
        description="调用internet_search工具，从互联网搜索引擎中检索得到问题相关的文档",
    )
    knowledge_base_search = KnowledgeBaseRetriever(id="knowledge_base_search_tool")
    internet_search = InternetRetriever(id="internet_search_tool")

    retrieving_toolkit.add_action(
        action=knowledge_base_retrieving,
        next_actions=[(internet_retrieving, 1)],
        prev_actions=[],
    )
    retrieving_toolkit.add_action(
        action=internet_retrieving,
        next_actions=[],
        prev_actions=[(knowledge_base_retrieving, 1)],
    )
    retrieving_toolkit.add_tool(
        tool=knowledge_base_search, connected_actions=[(knowledge_base_retrieving, 1)]
    )
    retrieving_toolkit.add_tool(tool=internet_search, connected_actions=[(internet_retrieving, 1)])

    operator_config = OperatorConfig(
        id="retrieving_operator",
        instruction=DOC_RETRIEVING_PROFILE + DOC_RETRIEVING_INSTRUCTION,
        output_schema=DOC_RETRIEVING_OUTPUT_SCHEMA,
        actions=[
            knowledge_base_retrieving,
            internet_retrieving,
        ],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=retrieving_toolkit),
    )

    return operator


def get_summarizing_operator():
    """Get the operator for document summarizing."""
    summarizing_toolkit = Toolkit()

    reference_listing = Action(
        id="doc_summarizing.reference_listing",
        name="原文出处列举",
        description="调用reference_list工具，以markdown格式返回推理过程中所涉及的原文出处链接，方便展示",
    )
    reference_list = ReferenceGenerator(id="reference_list_tool")

    summarizing_toolkit.add_action(
        action=reference_listing,
        next_actions=[],
        prev_actions=[],
    )
    summarizing_toolkit.add_tool(tool=reference_list, connected_actions=[(reference_listing, 1)])

    operator_config = OperatorConfig(
        id="summarizing_operator",
        instruction=DOC_SUMMARIZING_PROFILE + DOC_SUMMARIZING_INSTRUCTION,
        output_schema=DOC_SUMMARIZING_OUTPUT_SCHEMA,
        actions=[reference_listing],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=summarizing_toolkit),
    )

    return operator


def get_question_answering_workflow():
    """Get the workflow for question_answering and assemble the operators."""
    retrieving_operator = get_retrieving_operator()
    summarizing_operator = get_summarizing_operator()

    workflow = DbgptWorkflow()
    workflow.add_operator(
        operator=retrieving_operator,
        previous_ops=[],
        next_ops=[summarizing_operator],
    )
    workflow.add_operator(
        operator=summarizing_operator,
        previous_ops=[retrieving_operator],
        next_ops=None,
    )

    return workflow


def get_graph_question_answeing_expert_config(reasoner: Optional[Reasoner] = None) -> AgentConfig:
    """Get the expert configuration for graph Q&A."""

    expert_config = AgentConfig(
        profile=Profile(name="Graph Q&A Expert", description=DOC_SUMMARIZING_PROFILE),
        reasoner=reasoner or DualModelReasoner(),
        workflow=get_question_answering_workflow(),
    )

    return expert_config
