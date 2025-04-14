from app.core.common.type import ModelPlatformType, ReasonerType, WorkflowPlatformType
from app.core.model.message import TextMessage
from app.core.prompt.job_decomposition import (
    JOB_DECOMPOSITION_OUTPUT_SCHEMA,
    JOB_DECOMPOSITION_PROMPT,
)
from app.core.sdk.agentic_service import AgenticService
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.toolkit.toolkit import Action
from app.plugin.neo4j.resource.graph_modeling import (
    DocumentReader,
    EdgeLabelAdder,
    GraphReachabilityGetter,
    VertexLabelAdder,
)


def main():
    """Main function."""
    mas = AgenticService("Chat2Graph")

    # reasoner
    mas.reasoner(ReasonerType.DUAL)

    # toolkit
    mas.toolkit(
        (
            content_understanding_action,
            deep_recognition_action,
            relation_pattern_recognition_action,
            consistency_check_action,
        ),
    ).toolkit(
        (
            entity_type_definition_action,
            relation_type_definition_action,
            self_reflection_schema_action,
            schema_design_and_import_action,
            graph_validation_action,
        ),
    )

    # operator
    analysis_operator = (
        OperatorWrapper()
        .instruction(DOC_ANALYSIS_PROFILE + DOC_ANALYSIS_INSTRUCTION)
        .output_schema(DOC_ANALYSIS_OUTPUT_SCHEMA)
        .actions(
            [
                content_understanding_action,
                deep_recognition_action,
                relation_pattern_recognition_action,
                consistency_check_action,
            ]
        )
        .build()
    )
    concept_modeling_operator = (
        OperatorWrapper()
        .instruction(CONCEPT_MODELING_PROFILE + CONCEPT_MODELING_INSTRUCTION)
        .output_schema(CONCEPT_MODELING_OUTPUT_SCHEMA)
        .actions(
            [
                entity_type_definition_action,
                relation_type_definition_action,
                self_reflection_schema_action,
                schema_design_and_import_action,
                graph_validation_action,
            ]
        )
        .build()
    )
    job_decomposition_operator = (
        OperatorWrapper()
        .instruction(JOB_DECOMPOSITION_PROMPT)
        .output_schema(JOB_DECOMPOSITION_OUTPUT_SCHEMA)
        .build()
    )

    # leader & expert
    mas.leader(name="Leader").workflow(
        job_decomposition_operator, platform_type=WorkflowPlatformType.DBGPT
    ).build()

    mas.expert(name="Graph Modeling Expert").reasoner(
        thinker_name="Graph Modeling Expert", actor_name="Graph Modeling Expert"
    ).workflow(
        (analysis_operator, concept_modeling_operator), platform_type=ModelPlatformType.DBGPT
    ).build()

    # set the user message
    user_message = TextMessage(payload="通过工具来阅读原文，我需要对《三国演义》中的关系进行建模。")

    # submit the job
    service_message = mas.session().submit(user_message).wait()

    # print the result
    print(f"Service Result:\n{service_message.get_payload()}")


# tools
read_document = DocumentReader(id="read_document_tool")
vertex_label_generator = VertexLabelAdder(id="vertex_label_adder_tool")
edge_label_generator = EdgeLabelAdder(id="edge_label_adder_tool")
graph_reachability_getter = GraphReachabilityGetter(id="graph_reachability_getter_tool")

# actions
content_understanding_action = Action(
    id="doc_analysis.content_understanding",
    name="内容理解",
    description="通过阅读和批注理解文档的主要内容和结构",
    tools=[read_document],
)
deep_recognition_action = Action(
    id="doc_analysis.deep_recognition",
    name="核心概念识别",
    description="识别并提取文档中的关键概念和术语，对概念进行分类，建立层级关系。",
)
relation_pattern_recognition_action = Action(
    id="doc_analysis.relation_pattern",
    name="关系模式识别",
    description="发现概念间的关系模式和交互方式（结构模式、语义模式、演化模式）、提取概念网络特征（局部、全局、动态）。",
)
consistency_check_action = Action(
    id="doc_analysis.consistency_check",
    name="一致性检查",
    description="检查文档中的概念和关系是否一致，确保概念和关系已经对齐。并且没有孤立的概念（即，没有相邻的概念）",
)
entity_type_definition_action = Action(
    id="concept_modeling.entity_type",
    name="实体类型定义",
    description="定义和分类文档中识别出的核心实体类型，只需要分析即可",
)
relation_type_definition_action = Action(
    id="concept_modeling.relation_type",
    name="关系类型定义",
    description="设计实体间的关系类型和属性，只需要分析即可",
)
self_reflection_schema_action = Action(
    id="concept_modeling.reflection_schema",
    name="自我反思目前阶段的概念建模",
    description="不断检查和反思当前概念模型的设计，确保模型的完整性和准确性，并发现潜在概念和关系。最后确保实体关系之间是存在联系的，禁止出现孤立的实体概念（这很重要）。",
)
schema_design_and_import_action = Action(
    id="concept_modeling.schema_design_and_import",
    name="Schema设计创建 TuGraph labels",
    description="将概念模型转化为图数据库 labels，并在图数据中创建 labels",
    tools=[vertex_label_generator, edge_label_generator],
)
graph_validation_action = Action(
    id="concept_modeling.graph_validation",
    name="反思和检查图的可达性(Reachability)",
    description="需要调用相关的工具来检查。可达性指的是每个节点标签和关系标签都有至少一个节点或关系与之关联。如果不连通，则需要在目前的基础上调用工具来解决。",
    tools=[graph_reachability_getter],
)

# operation 1: Document Analysis
DOC_ANALYSIS_PROFILE = """
你是一位专业的文档分析专家，专注于从文档中提取关键信息，为知识图谱的构建奠定坚实基础。
你需要理解文档内容。请注意，你分析的文档可能只是全集的一个子集，需要通过局部推断全局。
请注意，你的任务不是需要操作图数据库。你的任务是分析文档，为后续的 knowledge graph modeling 提供重要信息。
"""  # noqa: E501

DOC_ANALYSIS_INSTRUCTION = """
请仔细阅读给定的文档，并按以下要求完成任务：

1. 语义层分析
   - 显式信息（比如，关键词、主题、术语定义）
   - 隐式信息（比如，深层语义、上下文关联、领域映射）

2. 关系层分析  
   - 实体关系（比如，直接关系、间接关系、层次关系）。时序关系（比如，状态变迁、演化规律、因果链条）

3. 知识推理
   - 模式推理、知识补全

请确保你的分析全面、细致，并为每一个结论提供充分的理由。
"""

DOC_ANALYSIS_OUTPUT_SCHEMA = """
{
    "domain": "文档所属领域的详细描述，解释该领域的主要业务和数据特点",
    "data_full_view": "对文档数据全貌的详细推测，包括数据结构、规模、实体关系等，并提供思考链路和理由",
    "concepts": [
        {"concept": "概念名称", "description": "概念的详细描述", "importance": "概念在文档中的重要性"},
        ...
    ],
    "properties": [
        {"concept": "所属概念", "property": "属性名称", "description": "属性的详细描述", "data_type": "属性的数据类型"},
        ...
    ],
    "potential_relations": [
        {"relation": "关系类型", "entities_involved": ["实体1", "实体2", ...], "description": "关系的详细描述", "strength": "关系的强度或重要性"},
        ...
    ],
    "document_insights": "其他重要（多条）信息或（多个）发现，它们独属于本文档的特殊内容，请用分号隔开。",
    "document_snippets": "文档中的关键片段，用于支撑你的分析结论，提供上下文信息。",
}
"""  # noqa: E501

# operation 2: Concept Modeling
CONCEPT_MODELING_PROFILE = """
你是一位知识图谱建模专家，擅长将概念和关系转化为图数据库模式。你需要设计合适的实体-关系模型，然后操作图数据库，确保任务的顺利完成。
"""

CONCEPT_MODELING_INSTRUCTION = """
你应该基于文档分析的结果，完成概念建模的任务，同时确保图建模的正确性和可达性。

1. 实体类型定义
- 从以下维度思考和定义实体类型：
  * 时间维度：事件、时期、朝代等时序性实体
  * 空间维度：地点、区域、地理特征等空间性实体
  * 社会维度：人物、组织、势力等社会性实体（可选）
  * 文化维度：思想、文化、典故等抽象实体（可选）
  * 物理维度：物品、资源、建筑等具象实体（可选）
- 建立实体类型的层次体系：
  * 定义上下位关系（如：人物-君主-诸侯）
  * 确定平行关系（如：军事人物、政治人物、谋士）
  * 设计多重继承关系（如：既是军事人物又是谋士）
- 为每个实体类型设计丰富的属性集：
  * 基础属性：标识符、名称、描述等
  * 类型特有属性：根据实体类型特点定义
  * 关联属性：引用其他实体的属性
- 考虑实体的时态性：
  * 属性的时效性（如：官职随时间变化）（可选）
  * 状态的可变性（如：阵营的转变）（可选）
- 为每个实体类型定义完整的属性集，包括必需属性和可选属性
- 确保实体类型之间存在潜在的关联路径，但保持概念边界的独立性

2. 关系类型设计
- 定义实体间的关系类型，包括直接关系、派生关系和潜在关系
- 明确关系的方向性（有向）、设计关系的属性集
- 通过关系组合，验证关键实体间的可达性
- （可选）考虑添加反向关系以增强图的表达能力

3. Schema生成
- 使用 graph schema creator 的函数，可以使用该函数生成 schema，为 vertex 和 edge 创建特殊的 schema。你不能直接写 cypher 语句，而是使用工具函数来帮助你操作数据库。
- 请注意：Schema 不是在 DB 中插入节点、关系等具体的数据，而是定义图数据库的模式（schema/label）。预期应该是定义是实体的类型、关系的类型、约束等这些东西。
- 任务的背景是知识图谱，所以，不要具体的某个实体，而是相对通用的实体。比如，可以从时间、抽象概念、物理实体和社会实体等多个主要维度来考虑。
- 需要多次读取 TuGraph 现有的 Schema，目的是确保根据 DDL 创建的 schema 符合预期。

4. 验证图的可达性
- 可达性是图数据库的核心特性之一，确保图中的实体和关系之间存在有效的连接路径，以支持复杂的查询需求。这在图建模中很重要，因为如果图不可达，将无法在构建一个完整的知识图谱。
- 通过查询图数据库，获取图的结构信息，验证实体和关系的可达性。
"""  # noqa: E501

CONCEPT_MODELING_OUTPUT_SCHEMA = """
{
    "reachability": "说明实体和关系之间的可达性，是否存在有效的连接路径",
    "stauts": "模型状态，是否通过验证等",
    "entity_label": "成功创建的实体标签",
    "relation_label": "成功创建的关系标签",
}
"""


if __name__ == "__main__":
    main()
