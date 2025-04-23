from app.core.common.system_env import SystemEnv
from app.core.common.type import ReasonerType, WorkflowPlatformType
from app.core.model.graph_db_config import Neo4jDbConfig
from app.core.model.message import HybridMessage, TextMessage
from app.core.prompt.job_decomposition import JOB_DECOMPOSITION_OUTPUT_SCHEMA
from app.core.sdk.agentic_service import AgenticService
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.toolkit.action import Action
from app.plugin.neo4j.resource.data_importation import (
    DataImport,
    DataStatusCheck,
    SchemaGetter,
)
from app.plugin.neo4j.resource.graph_analysis import (
    AlgorithmsGetter,
    BetweennessCentralityExecutor,
    CommonNeighborsExecutor,
    KMeansExecutor,
    LabelPropagationExecutor,
    LouvainExecutor,
    NodeSimilarityExecutor,
    PageRankExecutor,
    ShortestPathExecutor,
)
from app.plugin.neo4j.resource.graph_modeling import (
    DocumentReader,
    EdgeLabelAdder,
    GraphReachabilityGetter,
    VertexLabelAdder,
)
from app.plugin.neo4j.resource.graph_query import CypherExecutor, VertexQuerier
from app.plugin.neo4j.resource.question_answering import (
    InternetRetriever,
    KnowledgeBaseRetriever,
)
from app.plugin.neo4j.resource.system_checking import SystemStatusChecker

document_reader_tool = DocumentReader(id="document_reader_tool")
vertex_label_adder_tool = VertexLabelAdder(id="vertex_label_adder_tool")
edge_label_adder_tool = EdgeLabelAdder(id="edge_label_adder_tool")
graph_reachability_getter_tool = GraphReachabilityGetter(id="graph_reachability_getter_tool")
schema_getter_tool = SchemaGetter(id="schema_getter_tool")
data_status_check_tool = DataStatusCheck(id="data_status_check_tool")
data_import_tool = DataImport(id="data_import_tool")
cypher_executor_tool = CypherExecutor(id="cypher_executor_tool")
vertex_querier_tool = VertexQuerier(id="vertex_querier_tool")
algorithms_getter_tool = AlgorithmsGetter(id="algorithms_getter_tool")
page_rank_executor_tool = PageRankExecutor(id="page_rank_executor_tool")
betweenness_centrality_executor_tool = BetweennessCentralityExecutor(
    id="betweenness_centrality_executor_tool"
)
louvain_executor_tool = LouvainExecutor(id="louvain_executor_tool")
label_propagation_executor_tool = LabelPropagationExecutor(id="label_propagation_executor_tool")
shortest_path_executor_tool = ShortestPathExecutor(id="shortest_path_executor_tool")
node_similarity_executor_tool = NodeSimilarityExecutor(id="node_similarity_executor_tool")
common_neighbors_executor_tool = CommonNeighborsExecutor(id="common_neighbors_executor_tool")
kmeans_executor_tool = KMeansExecutor(id="kmeans_executor_tool")
knowledge_base_retriever_tool = KnowledgeBaseRetriever(id="knowledge_base_retriever_tool")
internet_retriever_tool = InternetRetriever(id="internet_retriever_tool")
system_status_checker_tool = SystemStatusChecker(id="system_status_checker_tool")

content_understanding_action = Action(
    id="content_understanding_action",
    name="content_understanding",
    description="通过阅读和批注理解文档的主要内容和结构（需要调用一个/些工具）",
    tools=[document_reader_tool],
)
deep_recognition_action = Action(
    id="deep_recognition_action",
    name="deep_recognition",
    description="识别被分析的文本中的关键概念和术语...",
    tools=[],
)
entity_type_definition_action = Action(
    id="entity_type_definition_action",
    name="entity_type_definition",
    description="定义和分类文档中识别出的核心实体类型",
    tools=[],
)
relation_type_definition_action = Action(
    id="relation_type_definition_action",
    name="relation_type_definition",
    description="设计实体间的关系类型和属性",
    tools=[],
)
schema_design_and_import_action = Action(
    id="schema_design_and_import_action",
    name="schema_design_and_import",
    description="将概念模型转化为图数据库 labels...",
    tools=[schema_getter_tool, vertex_label_adder_tool, edge_label_adder_tool],
)
graph_validation_action = Action(
    id="graph_validation_action",
    name="graph_validation",
    description="反思和检查图的可达性(Reachability)...",
    tools=[graph_reachability_getter_tool],
)
schema_understanding_action = Action(
    id="schema_understanding_action",
    name="schema_understanding",
    description="调用相关工具获取图模型...",
    tools=[schema_getter_tool],
)
data_status_check_action = Action(
    id="data_status_check_action",
    name="data_status_check",
    description="检查图数据库中当前数据的状态...",
    tools=[data_status_check_tool],
)
content_understanding_action_2 = Action(
    id="content_understanding_action_2",
    name="content_understanding_2",
    description="调用相关工具获取原始文本内容...",
    tools=[document_reader_tool],
)
triplet_data_generation_action = Action(
    id="triplet_data_generation_action",
    name="triplet_data_generation",
    description="根据图模型理解和文本内容理解...",
    tools=[data_import_tool],
)
output_result_action = Action(
    id="output_result_action",
    name="output_result",
    description="输出数据导入结果的汇总信息",
    tools=[],
)
vertex_type_and_condition_validation_action = Action(
    id="vertex_type_and_condition_validation_action",
    name="vertex_type_and_condition_validation",
    description="读取图数据现有的 schema...",
    tools=[schema_getter_tool],
)
supplement_action = Action(
    id="supplement_action",
    name="supplement",
    description="如查询条件/节点类型缺少或不匹配...",
    tools=[],
)
query_execution_action = Action(
    id="query_execution_action",
    name="query_execution",
    description="根据图查询语法、图现有 schema 和查询要求...",
    tools=[schema_getter_tool, cypher_executor_tool, vertex_querier_tool],
)
content_understanding_action_3 = Action(
    id="content_understanding_action_3",
    name="content_understanding_3",
    description="理解和分析用户的需求",
    tools=[],
)
algorithms_intention_identification_action = Action(
    id="algorithms_intention_identification_action",
    name="algorithms_intention_identification",
    description="确认需要执行的算法...",
    tools=[algorithms_getter_tool],
)
algorithms_execution_action = Action(
    id="algorithms_execution_action",
    name="algorithms_execution",
    description="调用相关的算法执行工具...",
    tools=[
        page_rank_executor_tool,
        betweenness_centrality_executor_tool,
        louvain_executor_tool,
        label_propagation_executor_tool,
        shortest_path_executor_tool,
        node_similarity_executor_tool,
        common_neighbors_executor_tool,
        kmeans_executor_tool,
        cypher_executor_tool,
        schema_getter_tool,
    ],
)
knowledge_base_retrieving_action = Action(
    id="knowledge_base_retrieving_action",
    name="knowledge_base_retrieving",
    description="调用knowledge_base_search工具...",
    tools=[knowledge_base_retriever_tool],
)
reference_listing_action = Action(
    id="reference_listing_action",
    name="reference_listing",
    description="以markdown格式返回推理过程中所涉及的原文出处链接...",
    tools=[],
)
query_system_status_action = Action(
    id="query_system_status_action",
    name="query_system_status",
    description="调用相关工具查询系统状态获取系统状态信息...",
    tools=[system_status_checker_tool, document_reader_tool],
)
job_decomposition_action = Action(
    id="job_decomposition_action",
    name="job_decomposition",
    description="按照相关的要求将任务，手动分解为多个子任务(job)...",
    tools=[],
)

analysis_operator = (
    OperatorWrapper()
    .instruction(
        """你是一位专业的文档分析专家，专注于从文档中提取关键信息，为知识图谱的构建奠定坚实基础。
      你需要理解文档内容。请注意，你分析的文档可能只是全集的一个子集，需要通过局部推断全局。
      请注意，你的任务不是需要操作图数据库。你的任务是分析文档，为后续的 knowledge graph modeling 提供重要信息。
      请确保你的分析全面、细致，并为每一个结论提供充分的理由。"""  # noqa: E501
    )
    .output_schema(
        """domain：文档所属领域的描述，帮助后续建模和数据抽取
      data_full_view：对文档数据全貌的详细推测，包括数据结构、规模、实体关系等，并提供思考链路和理由
      concepts：识别出的关键概念列表，每个概念包括名称、描述和重要性
        比如：
          concepts:
            - concept: "Person"
              description: "指文档中提及的历史人物"
              importance: ……
            - concept: "Event"
              description: "指文档中描述的历史事件"
              importance: ……
      properties：识别出的概念属性列表，每个属性包括所属概念、名称、描述和数据类型
        比如：
          properties:
            - concept: "Person"
              property: "birth_date"
              description: "出生日期"
              data_type: "date"
            - concept: "Event"
              property: "location"
              description: "事件发生地点"
              data_type: "string"
      potential_relations：识别出的潜在关系列表，每个关系包括类型、涉及的实体和描述
        比如：
          potential_relations:
            - relation: "participated_in"
              entities_involved: ["Person", "Event"]
              description: "指某人参与了某事件"
              strength: "strong"
            - relation: "located_in"
              entities_involved: ["Event", "Location"]
              description: "指事件发生在某地点"
              strength: "medium"
      document_insights：其他重要信息或发现，它们独属于本文档的特殊内容，请用分号隔开。比如，文档中提及的某些特定事件或概念的独特解释。
      document_snippets：文档中的关键片段，用于支撑你的分析结论，提供上下文信息。可以是原文摘录或重要段落。"""
    )
    .actions([content_understanding_action, deep_recognition_action])
    .build()
)

concept_modeling_operator = (
    OperatorWrapper()
    .instruction(
        """你是一位知识图谱建模专家，擅长将概念和关系转化为图数据库模式。你需要设计合适的实体

      你应该基于文档分析的结果，完成概念建模的任务，同时确保图建模的正确性和可达性。


      3. Schema生成
      - 使用 graph schema creator 的函数，可以使用该函数生成 schema，为 vertex 和 edge 创建特殊的 schema。你不能直接写 cypher 语句，而是使用工具函数来帮助你操作数据库。
      - 请注意：Schema 不是在 DB 中插入节点、关系等具体的数据，而是定义图数据库的模式（schema/label）。预期应该是定义是实体的类型、关系的类型、约束等这些东西。
      - 任务的背景是知识图谱，所以，不要具体的某个实体，而是相对通用的实体。比如，可以从时间、抽象概念、物理实体和社会实体等多个主要维度来考虑。
      - 需要多次读取 TuGraph 现有的 Schema，目的是确保根据 DDL 创建的 schema 符合预期。

      4. 验证图的可达性
      - 可达性是图数据库的核心特性之一，确保图中的实体和关系之间存在有效的连接路径，以支持复杂的查询需求。这在图建模中很重要，因为如果图不可达，将无法在构建一个完整的知识图谱。
      - 通过查询图数据库，获取图的结构信息，验证实体和关系的可达性。"""  # noqa: E501
    )
    .output_schema(
        """图 schema 可达性: 可达性分析结果，描述图中实体和关系之间的连接路径
      状态: schema 状态，是否通过验证
      实体标签: 成功创建的实体标签列表，例如：'Person', 'Organization'
      关系标签: 成功创建的关系标签列表，例如：'WorksAt', 'LocatedIn'"""
    )
    .actions(
        [
            content_understanding_action,
            deep_recognition_action,
            entity_type_definition_action,
            relation_type_definition_action,
            schema_design_and_import_action,
            graph_validation_action,
        ]
    )
    .build()
)

data_importation_operator = (
    OperatorWrapper()
    .instruction(
        """你是一位资深的图数据抽取专家。
      你的使命是，基于已分析的文档内容和图模型，精准地抽取关键信息，为构建知识图谱提供坚实的数据基础。
      在这一阶段，你不是在创造知识，而是在发掘隐藏在文档中的事实。
      你的目标是从文本中提取实体、关系和属性，请确保数据的准确、丰富、完整，因为后续的知识图谱构建将直接依赖于你抽取的数据质量。
      抽取数据完成后，你需要调用指定的工具，完成数据的导入。
      最后需要输出导入结果的总结。

      必须执行以下全部步骤：
      1. 调用相关工具获取图模型，并对图模型进行分析和理解
      2. 调用相关工具获取文本内容，并结合图模型进行分析和理解
      3. 根据对图模型理解和文本内容理解的结果，进行三元组数据的抽取（多次抽取），并存入图数据库中
      4. 输出数据导入结果"""
    )
    .output_schema(
        """输出结果：成功导入实体的数量、成功导入关系的数量；导入数据明细；（如果错误，原因是什么）"""
    )
    .actions(
        [
            schema_understanding_action,
            data_status_check_action,
            content_understanding_action_2,
            triplet_data_generation_action,
            output_result_action,
        ]
    )
    .build()
)

query_design_operator = (
    OperatorWrapper()
    .instruction(
        """你是一位专业的图数据库查询专家。
      你需要识别图查询的诉求，并校验查询的内容和对应的图模型是否匹配。如通过主键查询节点需要有指定的节点类型和明确的主键，如通过节点的普通属性查询需要指定节点类型、正确的属性筛选条件，并在模型上有对应的属性索引
      然后基于此，执行相关查询语句或者工具，从而获得数据库中的数据。
      如节点查询最常用的语法为 MATCH, WHERE, RETURN 等。你不具备写 Cypher 的能力，你只能调用工具来帮助你达到相关的目的。"""  # noqa: E501
    )
    .output_schema(
        """查询的内容：[用自然语言描述查询的内容]
      查询的结果：[如果查询成功，返回查询结果；如果查询失败，返回错误信息；r如果没有查询结果，用自然语言说明原因]"""
    )
    .actions(
        [vertex_type_and_condition_validation_action, supplement_action, query_execution_action]
    )
    .build()
)

algorithms_execute_operator = (
    OperatorWrapper()
    .instruction(
        """你是一个专业的图算法执行专家。你的工作是根据算法需求执行相应的图算法，并返回结果。
      注意，你不能够询问用户更多的信息。

      基于验证过的算法、算法参数，按要求完成算法执行任务：

      1.运行算法
      - 验证算法的可执行性（包括图数据库中是否支持该算法）
      - 按照算法的输入"""
    )
    .output_schema(
        """调用算法：调用的算法和参数（如果有多个算法）
      状态：算法执行的状态
      算法结果：算法执行的结果。如果失败，返回失败原因
      ...（格式自由）"""
    )
    .actions(
        [
            content_understanding_action_3,
            algorithms_intention_identification_action,
            algorithms_execution_action,
        ]
    )
    .build()
)

retrieving_operator = (
    OperatorWrapper()
    .instruction(
        """你是一位专业的文档检索专家。你的工作是，从知识库中检索与问题相关的文档，
      如果未能从知识库中检索到相关文档，直接结束任务返回空内容即可。
      仔细阅读检索得到的文档材料，分别总结每一份文档，为后续回答用户问题作准备。
      你阅读的文档未必与用户的问题直接相关，但是你仍然需要进行清晰全面的总结。
      你的任务是检索并总结文档，为后续推理得到最终的答案做铺垫。

      请认真理解给定的问题，同时，按要求完成任务：

      1.文档检索
      - 通过知识库检索得到与问题相关的文档
      2. 文档整理
      - 将知识库中检索得到各个文档分别总结为一段内容"""
    )
    .output_schema(
        """original_question: 输入的原始问题
      knowledge_base_result: 知识库中检索得到的相关内容总结
      knowledge_base_references: 知识库中检索得到的相关内容对应的章节或链接列表[1] ... [2] ..."""
    )
    .actions([knowledge_base_retrieving_action])
    .build()
)

summarizing_operator = (
    OperatorWrapper()
    .instruction(
        """你是一位文档总结专家,擅长总结归纳不同来源的文档。你需要根据用户的问题，总结归纳出用户需要的答案。

      基于检索得到的文档内容，根据具体的情况，完成以下文档总结任务:

      1. 分别总结不同来源的文档内容
      - 总结从知识库中检索得到问题相关内容

      2. 归纳不同来源的总结结果
      - 分析不同来源的文档总结的相同点与不同点
      - 归纳得出一份更完整的总结内容

      3. 答案生成
      - 分析问题的实际意图
      - 对用户提出的问题生成一个回答
      - 如果来自文档的内容对回答问题有所帮助，则参考来自文档的内容总结，优化回答内容
      - 如果回答中设计了来自知识库中的内容，提供回答中涉及的原文出处，给出一个List，其中包含markdown格式的原文链接
      - 如果没有检索到能帮助回答的相关文档，请你根据大模型自身的知识和经验，回答问题（避免你的 hallucination，不需要提供 reference）"""  # noqa: E501
    )
    .output_schema(
        """针对用户问题的最终回答，如果无法有效回答，则明确说明自己无法回答用户的问题
      references: 回答生成过程中参考的文档原文的markdown格式链接，比如 [1] ... [2] ..."""
    )
    .actions([reference_listing_action])
    .build()
)

leader_job_decomposition_operator = (
    OperatorWrapper()
    .instruction("Please check the current status of the system, and then decompose the task.")
    .output_schema(JOB_DECOMPOSITION_OUTPUT_SCHEMA)
    .actions([query_system_status_action, job_decomposition_action])
    .build()
)


def main():
    """Main function."""
    mas = AgenticService("Chat2Graph-Programmatic")

    mas.reasoner(ReasonerType.DUAL)

    mas.toolkit(content_understanding_action, deep_recognition_action)
    mas.toolkit(
        entity_type_definition_action,
        relation_type_definition_action,
        schema_design_and_import_action,
        graph_validation_action,
    ).toolkit(
        schema_understanding_action,
        data_status_check_action,
        content_understanding_action_2,
        triplet_data_generation_action,
        output_result_action,
    ).toolkit(
        vertex_type_and_condition_validation_action,
        supplement_action,
        query_execution_action,
    ).toolkit(
        content_understanding_action_3,
        algorithms_intention_identification_action,
        algorithms_execution_action,
    ).toolkit(knowledge_base_retrieving_action).toolkit(reference_listing_action).toolkit(
        query_system_status_action, job_decomposition_action
    )

    workflow_platform = WorkflowPlatformType.DBGPT
    mas.leader(name="Leader").workflow(
        leader_job_decomposition_operator, platform_type=workflow_platform
    ).build()

    mas.expert(
        name="Design Expert",
        description="""他是一位知识图谱建模(schema)专家。
        他的任务是根据具体的数据需求设计图的 Schema，明确定义顶点（Vertices）和边（Edges）的类型、属性及其关系。同时在图数据中创建/更新 Schema。
        他只能为某个特定的图数据库实例创建或修改数据结构（Schema）。
        他的输出是一个用于后续数据导入的清晰 Schema 定义。**他本身不处理具体数据（CURD），也绝不回答关于图数据库产品或技术本身的一般性介绍或询问。**""",  # noqa: E501
    ).workflow(
        (analysis_operator, concept_modeling_operator), platform_type=workflow_platform
    ).build()

    mas.expert(
        name="Extraction Expert",
        description="""他是一位原始数据抽取与数据导入图数据专家。
        他的前置要求是图 schema 在图数据库（不论是不是弱 schema 的数据库）中必须存在且已经定义了节点标签和边标签（否则专家将无法完成相关任务），且有明确的原始数据源（如文档、文件、数据库表、待处理文本，由用户上传）需要处理和导入到一个特定的图数据库实例。
        他的任务是：1. 根据已定义的 Schema 从原始数据中抽取结构化信息。 2. 将抽取的信息导入到目标图数据库中。
        他会输出数据导入过程的总结或状态报告。**他不负责设计 Schema、执行查询分析，也绝不提供关于图数据库技术或产品的一般性介绍。**""",  # noqa: E501
    ).workflow(data_importation_operator, platform_type=workflow_platform).build()

    mas.expert(
        name="Query Expert",
        description="""他是一位图数据查询专家。
        假设在一个已存在数据、且结构已知的特定图数据库实例上，需要执行精确查询以获取具体数据点或关系。
        他的任务是：1. 理解用户的具体查询意图。 2. 编写精确的图查询语句。 3. 在目标图数据库上执行查询。
        他会返回查询到的具体数据结果。**他不执行复杂的图算法分析，不负责建模或导入数据，也绝不回答关于图数据库概念、产品或技术本身的一般性问题。**""",
    ).workflow(query_design_operator, platform_type=workflow_platform).build()

    mas.expert(
        name="Analysis Expert",
        description="""他是一位图数据分析与算法应用专家。
        假设在一个已存在结构化数据、且需要进行超越简单查询的复杂网络分析（如社区发现、中心性计算等）的特定图数据库实例上。
        他的任务是根据分析目标，选择、配置并在目标图数据库上执行相应的图算法。
        他会返回算法执行的结果及其解释。**他不负责数据建模、导入、简单的节点/关系查找，也绝不提供关于图数据库技术或产品的一般性介绍。**""",
    ).workflow(algorithms_execute_operator, platform_type=workflow_platform).build()

    mas.expert(
        name="Q&A Expert",
        description="""他是一位通用问答与信息检索专家。
        **当任务是请求关于某个概念、技术、产品（例如，“介绍一下 Graph”）的一般性信息、定义、解释、比较或总结时，他是首选且通常是唯一的专家，** 尤其是当问题不涉及操作或查询一个具体的、已存在数据的图数据库实例时。
        他的任务是：1. 理解问题。 2. 从通用知识库、互联网或提供的文档中检索最相关的信息。 3. 综合信息并生成一个全面、清晰的回答。
        他会输出对问题的直接回答。**他完全不与任何项目特定的图数据库交互，不执行图查询或图算法，也不进行数据建模或导入。他专注于提供信息和解释，而非操作数据。** (类似于 RAG)""",  # noqa: E501
    ).workflow((retrieving_operator, summarizing_operator), platform_type=workflow_platform).build()

    mas.graph_db(
        graph_db_congfig=Neo4jDbConfig(
            name="MyGraphDB",
            host=SystemEnv.GRAPH_DB_HOST,
            port=SystemEnv.GRAPH_DB_PORT,
            type=SystemEnv.GRAPH_DB_TYPE,
        )
    )

    # set the user message
    user_message = TextMessage(payload="Please introduce TuGraph of Ant Group.")

    # submit the job
    service_message = mas.session().submit(user_message).wait()

    # print the result
    if isinstance(service_message, TextMessage):
        print(f"Service Result:\n{service_message.get_payload()}")
    elif isinstance(service_message, HybridMessage):
        text_message = service_message.get_instruction_message()
        print(f"Service Result:\n{text_message.get_payload()}")


if __name__ == "__main__":
    main()
