---
title: SDK
---

Chat2Graph SDK 提供了一套简洁的 API，用于构建和扩展智能体系统。其设计旨在分离组件职责，支持模块化和可扩展性，帮助开发者高效构建自己的智能体系统。

## 1. SDK 的分层设计

如图所示， Chat2Graph SDK 是分层的，下层的模块支持上层的模块。最顶层是**智能体（`Agent`）**，它代表了系统的核心执行单元和与用户交互的接口。智能体的具体行为和目标由其**配置（`Profile`）** 所定义，其任务的执行流程则通过**工作流（`Workflow`）** 进行编排。

工作流的执行依赖于下一层的引擎。**算子（`Operator`）** 作为任务执行的调度者，负责管理和驱动工作流中定义的步骤。为处理任务序列和依赖关系，算子利用 **DAG 任务图（`JobGraph`）** 来组织和追踪子任务。在执行过程中，**评估器（`Evaluator`）** 对算子中间结果或状态进行评估，以确保任务按预期方向推进。

这些上层组件的运作，依赖于基础能力层的支持：

* **推理器（`Reasoner`）** 是智能体认知能力的一部分，它封装了与大语言模型（LLM）的交互逻辑，使智能体能够进行理解、思考、规划和生成内容。
* **知识库（`KnowledgeBase`）** 为智能体提供持久化记忆和知识管理功能。它整合了记忆（`Memory`）、结构化知识（`Knowledge`），并能感知和利用系统**环境（`Environment`）** 信息。
* **工具包（`Toolkit`）** 则为智能体提供与外部世界交互和执行具体操作的机制。它通过定义一系列**工具（`Tool`）** 和**动作（`Action`）**，使得智能体能够调用外部 API、访问环境（`Environment`）或执行特定的计算（`Compute`）任务。

![](../../asset/image/sdk-yml.png)

通过这种层层支持的架构，Chat2Graph SDK 允许开发者组合和配置这些组件。高层组件定义任务目标和流程，而底层组件提供执行所需的能力。这种设计思路旨在将大语言模型的认知能力与软件工程中的数据处理、计算资源利用和流程控制等实践相结合，构建一个更加全面的智能体应用。

## 2. SDK API

### 2.1. Reasoner
<!-- WIP: Reasoner's API will be refined soon, and the documentation will be updated here. --> 

### 2.2. Toolkit
<!-- WIP: Reasoner's API will be refined soon, and the documentation will be updated here. -->

### 2.3. Agentic Service

Agentic Service 是 Chat2Graph SDK 的核心服务层，提供了完整的多代理系统管理和执行能力。该服务负责协调各个组件的初始化、配置和运行时交互。它在内部集成了多个服务组件，包括消息服务（`MessageService`）、会话服务（`SessionService`）、智能体服务（`AgentService`）、任务管理服务（`JobService`）、工具包服务（`ToolkitService`）和推理机服务（`ReasonerService`）。每个服务专注于特定的业务逻辑，同时通过统一的 Agentic Service 接口对外提供服务。

服务的执行流程采用任务驱动模式。当接收到用户消息时，系统会创建对应的 `Job` 对象，通过 `JobWrapper` 进行封装和提交。任务执行完成后，调用相关接口查询任务结果。


| 方法签名 | 描述 | 返回类型 |
|:---------|:-----|:---------|
| `session(session_id: Optional[str] = None) -> SessionWrapper` | 获取或创建会话实例 | `SessionWrapper` |
| `reasoner(reasoner_type: ReasonerType = ReasonerType.DUAL) -> AgenticService` | 配置推理器类型，支持链式调用 | `AgenticService` |
| `toolkit(*action_chain: Union[Action, Tuple[Action, ...]]) -> AgenticService` | 配置工具包动作链，支持链式调用 | `AgenticService` |
| `leader(name: str, description: Optional[str] = None) -> AgentWrapper` | 创建和配置 Leader 代理包装器 | `AgentWrapper` |
| `expert(name: str, description: Optional[str] = None) -> AgentWrapper` | 创建和配置 Expert 代理包装器 | `AgentWrapper` |
| `graph_db(graph_db_config: GraphDbConfig) -> AgenticService` | 配置图数据库连接 | `AgenticService` |
| `load(yaml_path: Union[str, Path], encoding: str = "utf-8") -> AgenticService` | 从 YAML 配置文件加载服务配置 | `AgenticService` |
| `execute(message: Union[TextMessage, str]) -> ChatMessage` | 同步执行用户消息，调用多智能体系统处理消息，返回结果（需要等待一定时间，约几分钟） | `ChatMessage` |

## 3. YAML 文件配置

Chat2Graph 支持通过 YAML 配置文件进行声明式的系统配置。配置文件采用分层结构，包含基本应用信息、插件、推理机、工具包、算子、工作流和智能体等多个部分。

配置文件的核心优势在于将系统的复杂配置外部化，使得不同的业务场景可以通过修改配置文件快速适配，而无需修改核心代码。工具和动作的配置采用引用机制，避免重复定义，提高可维护性。代理的工作流配置支持算子链和评估器的灵活组合，满足不同专家的特定需求。

通过 `AgenticService.load()` 方法，系统能够解析 YAML 配置并自动完成系统初始化等复杂的配置过程，大大简化了系统的部署和配置工作。

以下，我们提供一个包含注释的 YAML 参考文档，供用户理解和个性化配置：

```YAML
# 这是一个用于配置整个 Agentic System（智能体系统）的 YAML 文件。
# 它定义了应用的基础信息、可用的工具、智能体可以执行的动作、
# 执行特定任务的算子（Operators）、具有专门技能的专家（Experts）以及它们的工作流程。

# 应用基本信息配置
app:
  name: "Chat2Graph"  # 应用名称，例如："Chat2Graph"
  desc: "An Agentic System on Graph Database." # 应用描述，简要说明应用功能
  version: "0.0.1" # 应用版本号

# 插件配置
plugin:
  workflow_platform: "DBGPT" # 指定工作流依赖的平台，例如："DBGPT"

# 推理器配置
reasoner:
  type: "DUAL" # 指定推理器的类型，例如："SINGLE" (单推理器) 或 "DUAL" (双推理器，通常包含一个执行者 Actor 和一个思考者 Thinker)

# 工具定义：定义了一系列可供 Agent 使用的工具
# 每个工具通常包含名称 (name) 和模块路径 (module_path)
# "&tool_alias" 是一种 YAML 锚点，方便后续在 actions 中通过 "*tool_alias" 引用

# 关于工具 (Tools) 的说明：
# 1. 功能定位：工具主要用于执行那些大语言模型（LLM）自身无法直接完成的具体操作，或者和外界环境交互的具体操作。
#    这些工具内蕴含的操作通常是确定性的、易于通过代码实现的，例如：读取/写入文件、调用外部 API、执行数据库查询、进行精确计算等。
# 2. 实现方式：每个工具本质上是一个由代码（例如 Python 函数）实现的模块。
#    `module_path` 指向的就是这些代码实现。我们假设这些路径下的工具实现已经存在并且是可用的。
# 3. 系统的局限性限制了工具的可能集合：由于工具是基于预先编写的代码逻辑，它们不适合执行开放式的“生成”任务（如撰写文章、生成复杂图像、直接生成复杂的业务逻辑代码）
#    或那些难以用简单、确定性代码逻辑实现的工作。
#    如果，遇见必要的创造性或高度复杂的推理任务（例如，生成 HTML/CSS/JavaScript游戏代码），一般建议交给 LLM（即 Reasoner）自身承担。工具则辅助这些生成任务的后续步骤，如将生成的内容保存到文件。
# 此配置文件主要关注这些组件的编排和逻辑流程，而  非工具本身的开发。
tools:
  - &document_reader_tool # 工具锚点，方便后续引用
    name: "DocumentReader" # 工具的唯一名称
    module_path: "app.plugin.neo4j.resource.graph_modeling" # 工具的Python模块路径

  - &schema_getter_tool
    name: "SchemaGetter"
    module_path: "app.plugin.neo4j.resource.data_importation"

  - &file_writer_tool # HTML Tool Example
    name: "FileWriter"
    module_path: "app.tool_resource.html_tool"

  - &html_reader_tool # HTML Tool Example
    name: "HTMLReader"
    module_path: "other.tool_resource.html_tool"

  # ... (此处省略了其他工具定义，格式与上方类似)
  # 实际使用中，这里会列出所有可用的工具，例如：
  # - &vertex_label_adder_tool
  #   name: "VertexLabelAdder"
  #   module_path: "app.plugin.neo4j.resource.graph_modeling"
  # - &cypher_executor_tool
  #   name: "CypherExecutor"
  #   module_path: "app.plugin.neo4j.resource.graph_query"

# 动作定义：定义了 Agent 在执行任务时可以采取的具体动作
# 每个动作包含名称 (name)、描述 (desc)，以及完成该动作需要调用的工具 (tools)
actions:
  # 图建模相关动作示例
  - &content_understanding_action # 动作锚点
    name: "content_understanding" # 动作的唯一名称
    desc: "通过阅读和标注理解文档的主要内容和结构（需要调用一个或多个工具）。" # 动作的详细描述，解释其功能和目的
    tools: # 该动作执行时可能依赖的工具列表
      - *document_reader_tool # 引用之前定义的 document_reader_tool

  - &deep_recognition_action
    name: "deep_recognition"
    desc: | # 多行描述，详细说明动作的执行逻辑和思考维度
      识别分析文本（文本形式）中的关键概念和术语，对概念进行分类，发现概念之间的关系模式和交互方式，并建立层级关系。
      思考维度示例：
      1. 实体类型定义
         - 从时间、空间、社会、文化、物理等维度思考和定义实体类型。
         - 建立实体类型的层级体系。
      2. 关系类型设计
         - 定义实体间的关系类型，包括直接关系、派生关系和潜在关系。
    # tools: (如果此动作直接调用工具，则在此列出)

  # HTML/Web Development Related Actions Example
  - &generate_html_code_action
    name: "generate_dynamic_html_code"
    desc: "The LLM generates HTML, CSS, and JavaScript code for a visual and dynamic application based on user requirements. The output is the raw code string. This action itself does not use a tool, as the LLM handles generation."
    tools: []

  - &save_generated_code_action
    name: "save_code_to_file"
    desc: "Saves the provided code content to a specified HTML file. Example path: 'output/generated_page.html'."
    tools:
      - *file_writer_tool

  - &review_generated_html_action
    name: "review_html_code_functionality"
    desc: "Reads the content of a generated HTML file to assess if its structure and elements likely meet the user's functional requirements for a dynamic and visual application. Example path: 'output/generated_page.html'."
    tools:
      - *html_reader_tool

  # ... (此处省略了其他动作定义，格式与上方类似)
  # 实际使用中，这里会列出所有可定义的动作，例如：
  # - &schema_design_and_import_action
  #   name: "schema_design_and_import"
  #   desc: "将概念模型转化为图数据库标签，并使用相关工具在图数据库中创建图模式（如有必要，可多次调用工具并在数据库中创建标签，确保完成给定任务）（需要调用一个或多个工具）"
  #   tools:
  #     - *schema_getter_tool
  #     - *vertex_label_adder_tool # 假设已定义此工具

# 工具包定义：将相关的 actions 组合成工具包，供特定的 Operator 或 Expert 使用
# 每个工具包是一个 action 列表
toolkit:
  - [*content_understanding_action, *deep_recognition_action] # 第一个工具包，包含两个动作
  - [ # Web Development Toolkit Example
      *generate_html_code_action,
      *save_generated_code_action,
      *review_generated_html_action
    ]
  # - [ # 第二个工具包示例
  #     *entity_type_definition_action, # 假设已定义
  #     *relation_type_definition_action, # 假设已定义
  #     *schema_design_and_import_action, # 假设已定义
  #   ]
  # ... (此处省略了其他工具包定义)

# 算子 (Operator) 定义：Operator 是执行一系列相关 actions 的单元，通常对应任务的一个阶段。
# 每个 Operator 在执行其定义的 `actions` 时，会依赖一个 `Reasoner`（通常在 Expert层面统一配置或按需指定）。
# 这个 `Reasoner` 一般是由大语言模型（LLM）驱动的模块，它负责理解 `instruction`、
# 规划并调用 `actions` 中声明的 `tools`，并根据 `output_schema` 生成最终的响应或决策。
# 每个 Operator 的 `actions` 可以是一个列表，这些行为可以是顺序执行的，也可以是并行执行的。
# 每个 Operator 包含指令 (instruction)、输出模式 (output_schema) 和其可执行的动作 (actions)。
#
# Operator 执行机制补充说明：
# 1. 执行上下文：Operator 在执行时，会接收到一个丰富的上下文，包括：
#    - 当前 `Job` 的详细信息（如 `goal`, `context`）。
#    - 从 `KnowledgeBaseService` 检索到的相关 `Knowledge`。
#    - 通过 `FileService` 和 `MessageService` 提供的 `FileDescriptor`，用于访问相关文件内容。
#    - 前序 Operator 或 Expert 的输出 (`WorkflowMessage`)。
#    - 可能的 `lesson`（来自后续 Expert 的反馈，用于指导当前 Operator 的行为）。
# 2. Toolkit 交互配置：Operator 会从 Toolkit 中获取工具，这些工具与 Operator Config 中的 Actions 相关，从而使得 Operator 驱动的 Reasoner 拥有调用工具的能力。
operators:
  # 图建模算子示例
  - &analysis_operator # Operator 锚点
    instruction: | # 对 LLM 的指令，描述其角色、任务和注意事项
      你是一个专业的文档分析专家，专注于从文档中提取关键信息，为构建知识图谱打下坚实基础。
      你需要理解文档内容。请注意，你分析的文档可能只是完整集合的子集，需要你从局部细节推断全局情况。
    output_schema: | # 定义 Operator 输出内容的格式和结构，通常为 YAML 或 JSON 格式描述
      **domain**: 文档所属领域的描述，辅助后续建模和数据提取
      **concepts**: 识别出的关键概念列表，每个概念包括名称、描述和重要性
        *Example:*
          ```yaml
          concepts:
            - concept: "Person"
              description: "指文档中提到的人物"
              importance: "High"
          ```
      # ... (其他输出字段)
    actions: # 该 Operator 执行时按顺序或选择性调用的 actions 列表
      - *content_understanding_action
      - *deep_recognition_action

  # Web Development Operator Examples
  - &html_coding_operator
    instruction: |
      You are an expert web developer. The user has provided a request for an application.
      Your task is to generate a single HTML file containing all necessary HTML, CSS, and JavaScript to create a visual application that is dynamic and changes over time, based on this request.
      The code must be self-contained within this one file.
      The JavaScript part should be responsible for the dynamic behavior and time-based visual changes.
      The output of this step will be the raw code, which will then be saved to 'output/generated_page.html'.
    output_schema: |
      generated_code: text # The complete HTML/CSS/JS code as a single string.
      application_summary: Brief description of the generated application and its intended dynamic features.
    actions:
      - *generate_html_code_action # LLM executes this based on instruction
      - *save_generated_code_action # Uses the output from the LLM execution

  - &code_review_operator
    instruction: |
      You are a quality assurance specialist. An HTML file has been generated and saved at 'output/generated_page.html' based on a user's request for a dynamic and visual application.
      Your task is to:
      1. Read the content of this HTML file.
      2. Based *only* on the code structure, elements, and embedded scripts, assess if it appears to fulfill the original user request for a visual, dynamic, and time-varying application.
      3. Look for JavaScript that manipulates the DOM over time, uses timers/animations, or event handling that suggests dynamic behavior.
      4. Check for HTML structures that would result in a visual output.
      Provide feedback on whether the code seems to meet these requirements.
    output_schema: |
      review_passed: boolean # True if the code appears to meet requirements, False otherwise.
      feedback: Detailed comments on how the code meets or misses the dynamic and visual requirements. Identify specific HTML/CSS/JS parts that support your assessment. Include suggestions for improvement if necessary.
      path_to_reviewed_file: "output/generated_page.html" # Path to the file that was reviewed
    actions:
      - *review_generated_html_action

  # ... (此处省略了其他算子定义，格式与上方类似)
  # 例如，数据导入算子：
  # - &data_importation_operator
  #   instruction: "你是一个资深的图数据提取专家..."
  #   output_schema: "**Output Results**: 成功导入的实体数量，成功导入的关系数量..."
  #   actions:
  #     - *schema_understanding_action # 假设已定义
  #     - *triplet_data_generation_action # 假设已定义

# 专家 (Expert) 定义：Expert 是更高层次的抽象，代表具有特定能力的智能体
# 每个 Expert 包含简介 (profile)、推理器配置 (reasoner) 和工作流 (workflow)
# workflow 由一个或多个 Operator 组成。Expert 通过其配置的 `reasoner` 来驱动 `workflow` 中 `Operator` 的执行。
#
# Workflow 机制说明：
# 1. Operator 编排：`workflow` 中定义的 Operator 列表不仅是简单的序列，它们可以构成一个执行图（Operator Graph）。
#    Expert 按照这个图的结构和依赖关系来执行 Operators。
# 2. 信息传递：Operators 之间以及 Expert 与其内部 Operators 之间通过 `WorkflowMessage` 对象传递数据和状态。
#    这个消息对象承载了每个步骤的输出、状态以及可能的错误信息。
# 3. 评估机制：Workflow 的执行可以（可能）包含一个特殊的 `EvalOperator`。这个评估算子负责在 Workflow 执行的
#    关键节点或最终阶段，对到目前为止的进展或产出质量进行评估，其评估结果可以影响后续的流程。
experts:
  - profile: # 专家的简介信息
      name: "Design Expert" # 专家的名称
      desc: | # 专家的详细描述，说明其能力、任务范围和限制。请使用第三人称。
        他是一位知识图谱建模（模式）专家。
        他的任务是根据特定的数据需求设计图的 Schema，清晰定义顶点（Vertices）和边（Edges）的类型、属性及关系。同时，他在图数据中创建/更新 Schema。
        他只对特定的图数据库实例创建或修改数据结构（Schema）。
        他的输出是为后续数据导入提供清晰的 Schema 定义。**他本人不处理具体数据（CRUD），也从不回答关于图数据库产品或技术本身的一般性介绍或咨询。**
    reasoner: # 该专家使用的推理器配置，这个 reasoner 会被其 workflow 中的 Operators 使用
      actor_name: "Design Expert" # 指定 Actor 的名称
      thinker_name: "Design Expert" # 指定 Thinker 的名称 (如果 reasoner.type 为 DUAL)
    workflow: # 该专家执行任务时的工作流，由一个或多个 Operator 列表组成
      - [*analysis_operator, *concept_modeling_operator] # 此工作流包含两个 Operator (假设 concept_modeling_operator 已定义)

  # Web Development Expert Example
  - profile:
      name: "WebDevExpert"
      desc: |
        This expert specializes in generating and reviewing HTML, CSS, and JavaScript code
        for dynamic and visual web applications. It first generates and saves the code,
        then reviews the generated code to assess its adherence to requirements.
    reasoner:
      actor_name: "WebDevActor"
      thinker_name: "WebDevThinker"
    workflow:
      - [*html_coding_operator, *code_review_operator] # Sequential workflow

  # ... (此处省略了其他专家定义，格式与上方类似)

# 领导者 (Leader) 配置：负责任务分解和协调
# Leader 机制说明：
# 1. JobGraph 管理：当 Leader 执行时，它不仅仅是分解任务，
#    而是将原始任务转化为一个子任务图（JobGraph），这是一个有向无环图 (DAG)，定义了子任务（SubJob）及其依赖关系。
# 2. 动态调度与执行：Leader 负责调度和执行 JobGraph：
#    - 并行处理：无依赖或依赖已完成的子任务会被并行调度执行。
#    - Expert 反馈处理：Leader 会根据 Expert 执行子任务后返回的状态（通过 WorkflowMessage）动态调整 JobGraph 的执行。例如：
#      - `INPUT_DATA_ERROR`：可能导致相关前置任务被重新规划或执行。
#      - `JOB_TOO_COMPLICATED_ERROR`：Expert 认为子任务过复杂，Leader 会将该子任务视为新的原始任务进行再次分解，深化 JobGraph。
leader:
  actions: # Leader 可以执行的动作，通常用于任务分解和状态查询
    - *query_system_status_action # 假设已定义
    - *job_decomposition_action # 假设已定义

# 知识库配置 (可留空)
knowledgebase: {}

# 记忆模块配置 (可留空)
memory: {}

# 环境变量配置 (可留空)
env: {}
```

## 4. 系统环境配置

Chat2Graph 管理环境变量，通过 `SystemEnv` 类提供统一的配置访问接口。该设计允许系统从多个来源获取配置值，并按照优先级进行覆盖。

其环境变量配置主要包括，大语言模型和嵌入模型调用参数、数据库配置、知识库配置、大模型默认生成语言以及系统运行参数等。开发者可以通过修改 `.env` 文件或设置环境变量来快速调整系统参数（可以通过全局搜索对应环境变量，查找源码，来深入了解每个参数的功能）。

环境变量的赋值优先级顺序为：`.env` 文件配置 > 操作系统环境变量 > 系统默认值。当系统启动时，`SystemEnv` 会自动加载 `.env` 文件中的配置（只加载一次），并将其与操作系统环境变量和预定义的默认值进行合并。每个环境变量都具有明确的类型定义和默认值，系统会自动进行类型转换和验证（支持类型转换的类型有：`bool`、`str`、`int`、`float` 以及自定义枚举类型如 `WorkflowPlatformType`、`ModelPlatformType` 等）。

此外，环境变量配置管理采用延迟加载和缓存机制。环境变量值在首次访问时被解析和缓存，后续访问直接从缓存中获取。同时，系统支持运行时动态修改配置值，方便调试和测试。

### 4.1. 模型兼容性说明

Chat2Graph 支持所有兼容 OpenAI API 标准的大语言模型和嵌入模型，包括但不限于：

**大语言模型支持**：

- Google Gemini 系列（Gemini 2.0 Flash、Gemini 2.5 Flash、Gemini 2.5 Pro 等，必须选择[兼容 OpenAI 接口](https://ai.google.dev/gemini-api/docs/openai)的版本）
- OpenAI 系列（GPT-4o、o3-mini 等）
- Anthropic Claude 系列（Claude Opus 4、Claude Sonnet 4、Claude Sonnet 3.7、Claude Sonnet 3.5 等，必须选择[兼容 OpenAI 接口](https://docs.anthropic.com/en/api/openai-sdk)的版本）
- 阿里通义千问系列（Qwen-3）
- 智谱 GLM 系列
- DeepSeek 系列
- 以及其他支持 OpenAI API 格式的模型服务，比如硅基流动等

**嵌入模型支持**：

- OpenAI Embedding 系列（text-embedding-3-small、text-embedding-3-large 等）
- Gemini Embedding 系列（选择兼容 OpenAI 接口的版本）
- 阿里通义千问嵌入模型（text-embedding-v3 等）
- 其他兼容 OpenAI Embeddings API 的模型

只需在 `.env` 文件中配置相应的模型名称、API 端点和密钥即可使用。系统会自动处理不同模型服务商的 API 调用细节。根据测试经验，推荐使用 Gemini 2.0 Flash、Gemini 2.5 Flash 或 o3-mini 等模型以获得更好的推理效果和性价比。

## 5. 示例

* YAML 配置构建：`test/example/agentic_service/load_service_by_yaml.py`
  * 系统默认 YAML 配置示例: `app/core/sdk/chat2graph.yml`
* SDK 编程式构建：`test/example/agentic_service/load_service_by_sdk.py`
* 无会话服务执行：`test/example/agentic_service/run_agentic_service_without_session.py`
* 会话服务执行：`test/example/agentic_service/run_agentic_service_with_session.py`
