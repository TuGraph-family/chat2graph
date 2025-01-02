import asyncio
from typing import List, Optional, Tuple
from uuid import uuid4

from app.agent.job import Job
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.workflow.operator.operator import Operator, OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit, ToolkitService

# operation 1: Document Retrieving
DOC_RETRIEVING_PROFILE = """
你是一位专业的文档检索专家。你的工作是，阅读提供的文档材料，分别总结每一份文档，为后续回答用户问题作准备。
你阅读的文档未必与用户的问题直接相关，但是你仍然需要进行清晰全面的总结。
你的任务是总结文档，为后续推理得到最终的答案做铺垫。
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

# operation 1: Document Summarizing
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
TuGraph 是蚂蚁集团自主研发的大规模图计算系统，提供图数据库引擎和图分析引擎。
其主要特点是大数据量存储和计算，高吞吐率，以及灵活的 API，同时支持高效的在线事务处理（OLTP）和在线分析处理（OLAP）。
LightGraph、GeaGraph 是 TuGraph 的曾用名。

主要功能特征包括：
标签属性图模型
支持多图
完善的 ACID 事务处理
内置 34 图分析算法
基于 web 客户端的图可视化工具
支持 RESTful API 和 RPC
OpenCypher 图查询语言
基于 C++/Python 的存储过程
适用于高效图算法开发的 Traversal API

性能及可扩展性特征包括：
TB 级大容量
千万点/秒的高吞吐率
高可用性支持
高性能批量导入
在线/离线备份
""",
    """
TuGraph 可以通过 Docker Image 快速安装，或者通过 rpm/deb 包本地安装。另外TuGraph在阿里云计算巢上提供了社区版服务，您无需自行购置云主机，即可在计算巢上快速部署TuGraph服务、实现运维监控，从而搭建您自己的图应用。

安装包/镜像下载：参考下载地址中的“TuGraph最新版本”章节。

计算巢部署：可以在阿里云计算巢自行搜索，也可以通过部署链接快速访问。
""",
]

TUGRAPH_REF = ["快速上手-简介", "快速上手-安装"]

INTERNET_DOC = [
    """
Contents:
本文主要介绍TuGraph社区版的主要功能和特性，以及TuGraph企业版和社区版的差异。
TuGraph图数据库由蚂蚁集团与清华大学联合研发，构建了一套包含图存储、图计算、图学习、图研发平台的完善的图技术体系，拥有业界领先规模的图集群，解决了图数据分析面临的大数据量、高吞吐率和低延迟等重大挑战，是蚂蚁集团金融风控能力的重要基础设施，显著提升了欺诈洗钱等金融风险的实时识别能力和审理分析效率，并面向金融、工业、政务服务等行业客户。
2022年9月，TuGraph单机版开源，提供了完备的图数据库基础功能和成熟的产品设计，支持TB级别的数据规模，为用户管理和分析复杂关联数据提供了高效、易用、可靠的平台。
TuGraph社区版于2022年9月开源，提供了完整的图数据库基础功能和成熟的产品设计（如ACID兼容的事务、编程API和配套工具等），适用于单实例部署。社区版支持TB级别的数据规模，为用户管理和分析复杂关联数据提供了高效、易用、可靠的平台，是学习TuGraph和实现小型项目的理想选择。
TuGraph是支持大数据量、低延迟查找和快速图分析功能的高效图数据库。TuGraph也是基于磁盘的数据库，支持存储多达数十TB的数据。TuGraph提供多种API，使用户能够轻松构建应用程序，并使其易于扩展和优化。
它具有如下功能特征：
属性图模型
实时增删查改
多重图（点间允许多重边）
多图（大图与多个子图）
完善的ACID事务处理，隔离级别为可串行化（serializable）
点边索引、全文索引
混合事务和分析处理（HTAP），支持图查询、图分析、图学习
主流图查询语言（OpenCypher、ISO GQL等）
支持OLAP API，内置30多种图分析算法
基于C++/Python的存储过程，含事务内并行Traversal API
提供图可视化工具
在性能和可扩展性方面的支持：
千万点/秒的高吞吐率
TB级大容量
高可用性支持
高性能批量导入
在线/离线的备份恢复
TuGraph是一个具备多图能力的强类型、有向属性图数据库。
图项目：每个数据库服务可以承载多个图项目（多图），每个图项目可以有自己的访问控制配置，数据库管理员可以创建或删除指定图项目。
点：指实体，一般用于表达现实中的实体对象，如一部电影、一个演员。
主键：用户自定义的点数据主键，默认唯一索引，在对应的点类型中唯一。
VID：点在存储层自动分配图项目中的唯一ID，用户不可修改。
上限：每个图项目存储最多2^(40)个点数据。
边：用于表达点与点之间的关系，如演员出演电影。
有向边：边为有向边。若要模拟无向边，用户可以创建两个方向相反的边。
多条边：两个点数据之间可以有多条边数据。当前TuGraph支持重复边，如要确保边边唯一，需要通过业务策略实现。
上限：两个点数据之间存储最多2^(32)条边数据。
属性图：点和边可以具有与其关联的属性，每个属性可以有不同的类型。
强类型：每个点和边有且仅有一个标签，创建标签后，修改属性数量及类型有代价。
指定边的起/终点类型：可限制边的起点和终点点类型，支持同类型边的起点和终点的点类型不同，如个人转账给公司、公司转账给公司；当指定边的起/终点类型后，可增加多组起/终点类型，不可删除已限制的起/终点类型。
无限制模式：支持不指定边的起点和终点的点类型，任意两个点类型间均可创建该类型的边数据。注：当指定边的起/终点类型后无法再采用无限制模式。
TuGraph支持多种可用于属性的数据类型。具体支持的数据类型如下：
数据类型
最小值
最大值
描述
BOOL
false
true
布尔值
INT8
-128
127
""",
    """
Contents:
此文档主要用于新用户快速上手，其中包含了 TuGraph 的简介、特征、安装和使用。
TuGraph 是蚂蚁集团自主研发的大规模图计算系统，提供图数据库引擎和图分析引擎。其主要特点是大数据量存储和计算，高吞吐率，以及灵活的 API，同时支持高效的在线事务处理（OLTP）和在线分析处理（OLAP）。 LightGraph、GeaGraph 是 TuGraph 的曾用名。
主要功能特征包括：
标签属性图模型
支持多图
完善的 ACID 事务处理
内置 34 图分析算法
基于 web 客户端的图可视化工具
支持 RESTful API 和 RPC
OpenCypher 图查询语言
基于 C++/Python 的存储过程
适用于高效图算法开发的 Traversal API
性能及可扩展性特征包括：
TB 级大容量
千万点/秒的高吞吐率
高可用性支持
高性能批量导入
在线/离线备份
TuGraph 无论是物理、虚拟还是容器化环境，均支持 X86_64 和 ARM64 架构的的平台。
目前我们建议用户使用 NVMe SSD 配合较大的内存配置以获取最佳性能。
硬件
最低配置
建议配置
CPU
X86_64
Xeon E5 2670 v4
内存
4GB
256GB
硬盘
100GB
1TB NVMe SSD
操作系统
Linux 2.6
Ubuntu 18.04, CentOS 7.3
TuGraph 可以通过 Docker Image 快速安装，或者通过 rpm/deb 包本地安装。另外TuGraph在阿里云计算巢上提供了社区版服务，您无需自行购置云主机，即可在计算巢上快速部署TuGraph服务、实现运维监控，从而搭建您自己的图应用。
None
None
本地安装 docker 环境
参考 docker 官方文档：https://docs.docker.com/get-started/
拉取镜像
启动docker
启动 TuGraph 服务可以通过两种方式来实现。第一种方式将镜像拉取与服务启动整合在一起，用户只需执行运行容器的操作，即可同时启动 TuGraph 服务。第二种方式则是在创建 TuGraph 容器后，手动进入容器内部以触发服务启动。尽管这种方法初期步骤稍显繁琐，但在如忘记密码的情况下，它提供了更灵活的密码重置选项。
方式一
方式二
前端访问
None
None
© 版权所有 2023, Ant Group.
""",
]

INTERNET_REF = [
    "https://tugraph-db.readthedocs.io/zh-cn/v4.0.0/2.introduction/3.what-is-tugraph.html",
    "https://tugraph-db.readthedocs.io/zh-cn/latest/3.quick-start/1.preparation.html",
]

REFERENCE_LIST = """
[引用1](https://tugraph-db.readthedocs.io/zh-cn/latest/2.introduction/3.what-is-tugraph.html)
[引用2](https://tugraph-db.readthedocs.io/zh-cn/latest/2.introduction/4.schema.html)
[引用3](https://tugraph-db.readthedocs.io/zh-cn/latest/2.introduction/5.characteristics/1.performance-oriented.html)
"""


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
        """Retrive a list of related contents and a list of their reference name from knowledge base given the question.

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
        """Retrive a list of related webpage contents and a list of their URL references from Internet given the question.

        Args:
            question (str): The question asked by user.

        Returns:
            Tuple[List[str], List[str]]: The list of related webpage contents and the list of URL references.
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
        description="从外接知识库中检索问题得到相关内容",
    )
    internet_retrieving = Action(
        id="doc_retrieving.internet_retrieving",
        name="互联网检索",
        description="从互联网搜索引擎中检索得到问题相关内容",
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
    retrieving_toolkit.add_tool(
        tool=internet_search, connected_actions=[(internet_retrieving, 1)]
    )

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
        description="以markdown格式返回推理过程中所涉及的原文出处链接，方便展示",
    )
    reference_list = ReferenceGenerator(id="reference_list_tool")

    summarizing_toolkit.add_action(
        action=reference_listing,
        next_actions=[],
        prev_actions=[],
    )
    summarizing_toolkit.add_tool(
        tool=reference_list, connected_actions=[(reference_listing, 1)]
    )

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


async def main():
    """Main function"""
    workflow = get_question_answering_workflow()

    job = Job(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="TuGraph是什么？",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
