---
title: SDK
---

The Chat2Graph SDK provides a concise set of APIs for building and extending agent systems. Its design focuses on separating component responsibilities while supporting modularity and extensibility, helping developers efficiently construct their own agent systems.

## 1. Layered Design of the SDK

As shown in the diagram, the Chat2Graph SDK is layered, with lower-level modules supporting upper-level ones. At the top is the **Agent**, representing the core execution unit and user interaction interface of the system. An agent's specific behaviors and objectives are defined by its **Profile**, while its task execution flow is orchestrated through **Workflow**.

Workflow execution relies on the next layer of engines. The **Operator**, as the task execution scheduler, manages and drives the steps defined in the workflow. To handle task sequences and dependencies, operators use **DAG JobGraph** to organize and track subtasks. During execution, the **Evaluator** assesses intermediate results or states to ensure tasks progress as expected.

The operation of these upper-level components depends on foundational capabilities:

* **Reasoner** is part of the agent's cognitive abilities, encapsulating interaction logic with large language models (LLMs) to enable understanding, reasoning, planning, and content generation.
* **KnowledgeBase** provides the agent with persistent memory and knowledge management functions. It integrates Memory, structured Knowledge, and can perceive and utilize **Environment** information.
* **Toolkit** equips the agent with mechanisms to interact with the external world and perform specific operations. By defining a series of **Tools** and **Actions**, it enables the agent to call external APIs, access the Environment, or execute specific computational tasks.

![](../../asset/image/sdk-yml.png)

Through this layered architecture, the Chat2Graph SDK allows developers to combine and configure these components. High-level components define task objectives and flows, while lower-level components provide execution capabilities. This design aims to integrate the cognitive abilities of LLMs with software engineering practices like data processing, computational resource utilization, and workflow control to build more comprehensive agent applications.

## 2. SDK API

### 2.1. Reasoner
<!-- WIP: Reasoner's API will be refined soon, and the documentation will be updated here. --> 

### 2.2. Toolkit
<!-- WIP: Reasoner's API will be refined soon, and the documentation will be updated here. -->

### 2.3. Agentic Service

Agentic Service is the core service layer of Chat2Graph SDK, providing comprehensive multi-agent system management and execution capabilities. It coordinates the initialization, configuration, and runtime interactions of various components. Internally, it integrates multiple service components including MessageService, SessionService, AgentService, JobService, ToolkitService, and ReasonerService. Each service focuses on specific business logic while offering unified Agentic Service interfaces externally.

The service execution follows a task-driven model. When receiving a user message, the system creates a corresponding Job object, encapsulates it with JobWrapper, and submits it. After task completion, relevant interfaces are called to query the results.


| Method Signature | Description | Return Type |
|:---------|:-----|:---------|
| `session(session_id: Optional[str] = None) -> SessionWrapper` | Gets or creates a session instance | `SessionWrapper` |
| `reasoner(reasoner_type: ReasonerType = ReasonerType.DUAL) -> AgenticService` | Configures the reasoner type, supporting method chaining | `AgenticService` |
| `toolkit(*action_chain: Union[Action, Tuple[Action, ...]]) -> AgenticService` | Configures the toolkit action chain, supporting method chaining | `AgenticService` |
| `leader(name: str, description: Optional[str] = None) -> AgentWrapper` | Creates and configures a Leader agent wrapper | `AgentWrapper` |
| `expert(name: str, description: Optional[str] = None) -> AgentWrapper` | Creates and configures an Expert agent wrapper | `AgentWrapper` |
| `graph_db(graph_db_config: GraphDbConfig) -> AgenticService` | Configures graph database connection | `AgenticService` |
| `load(yaml_path: Union[str, Path], encoding: str = "utf-8") -> AgenticService` | Loads service configuration from a YAML file | `AgenticService` |
| `execute(message: Union[TextMessage, str]) -> ChatMessage` | Synchronously executes a user message, invoking the multi-agent system to process the message and return results (may take several minutes) | `ChatMessage` |

## 3. YAML Configuration

Chat2Graph supports declarative system configuration via YAML files. The configuration file adopts a hierarchical structure, including basic application info, plugins, reasoners, toolkits, operators, workflows, and agents.

The core advantage of YAML configuration is externalizing complex system setups, allowing quick adaptation to different business scenarios without modifying core code. Tool and action configurations use reference mechanisms to avoid redundancy and improve maintainability. Agent workflows support flexible combinations of operator chains and evaluators to meet diverse expert requirements.

Through the `AgenticService.load()` method, the system parses YAML configurations and automatically completes complex setup processes like initialization, significantly simplifying deployment and configuration.

Below is an annotated YAML reference document for understanding and customization:

```yaml
# This is a YAML file for configuring the entire Agentic System.
# It defines the application's basic info, available tools, agent-executable actions,
# operators for specific tasks, specialists (Experts), and their workflows.

# Basic application configuration
app:
  name: "Chat2Graph"  # Application name, e.g., "Chat2Graph"
  desc: "An Agentic System on Graph Database." # Brief description of the application
  version: "0.0.1" # Version number

# Plugin configuration
plugin:
  workflow_platform: "DBGPT" # Workflow dependency platform, e.g., "DBGPT"

# Reasoner configuration
reasoner:
  type: "DUAL" # Reasoner type, e.g., "SINGLE" (single reasoner) or "DUAL" (dual reasoner, typically including an Actor and a Thinker)

# Tool definitions: A series of tools available for agents
# Each tool usually includes a name (name) and module path (module_path)
# "&tool_alias" is a YAML anchor for referencing in actions via "*tool_alias"

# Notes on Tools:
# 1. Purpose: Tools mainly execute operations that LLMs cannot directly perform or interact with the external environment.
#    These operations are typically deterministic and easily implemented via code, e.g., reading/writing files, calling external APIs, executing database queries, or precise calculations.
# 2. Implementation: Each tool is essentially a code module (e.g., Python function).
#    `module_path` points to these implementations, assumed to be pre-existing and functional.
# 3. System limitations constrain possible tools: Since tools rely on predefined logic, they are unsuitable for open-ended "generation" tasks (e.g., writing articles, creating complex images, or generating intricate business logic code).
#    For creative or highly complex reasoning tasks (e.g., generating HTML/CSS/JavaScript game code), it's recommended to delegate them to LLMs (i.e., Reasoners), with tools assisting subsequent steps like saving generated content.
# This configuration focuses on component orchestration and logic flows, not tool development.
tools:
  - &document_reader_tool # Tool anchor for referencing
    name: "DocumentReader" # Unique tool name
    module_path: "app.plugin.neo4j.resource.graph_modeling" # Python module path

  - &schema_getter_tool
    name: "SchemaGetter"
    module_path: "app.plugin.neo4j.resource.data_importation"

  - &file_writer_tool # HTML Tool Example
    name: "FileWriter"
    module_path: "app.tool_resource.html_tool"

  - &html_reader_tool # HTML Tool Example
    name: "HTMLReader"
    module_path: "other.tool_resource.html_tool"

  # ... (other tool definitions omitted here, similar in format)
  # In practice, all available tools would be listed, e.g.:
  # - &vertex_label_adder_tool
  #   name: "VertexLabelAdder"
  #   module_path: "app.plugin.neo4j.resource.graph_modeling"
  # - &cypher_executor_tool
  #   name: "CypherExecutor"
  #   module_path: "app.plugin.neo4j.resource.graph_query"

# Action definitions: Specific actions agents can take during task execution
# Each action includes a name (name), description (desc), and required tools (tools)
actions:
  # Graph modeling action examples
  - &content_understanding_action # Action anchor
    name: "content_understanding" # Unique action name
    desc: "Understands a document's main content and structure through reading and annotation (may invoke one or more tools)." # Detailed description
    tools: # Tools required for this action
      - *document_reader_tool # References the document_reader_tool

  - &deep_recognition_action
    name: "deep_recognition"
    desc: | # Multi-line description explaining execution logic and dimensions
      Identifies key concepts and terms in text, classifies concepts, discovers relationship patterns, and establishes hierarchies.
      Example dimensions:
      1. Entity type definition
         - Defines entity types from temporal, spatial, social, cultural, and physical perspectives.
         - Builds hierarchical systems for entity types.
      2. Relationship type design
         - Defines relationship types between entities, including direct, derived, and potential relationships.
    # tools: (If this action directly invokes tools, list them here)

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

  # ... (other action definitions omitted here, similar in format)

# Toolkit definitions: Groups related actions into toolkits for specific Operators or Experts
# Each toolkit is a list of actions
toolkit:
  - [*content_understanding_action, *deep_recognition_action] # First toolkit with two actions
  - [ # Web Development Toolkit Example
      *generate_html_code_action,
      *save_generated_code_action,
      *review_generated_html_action
    ]
  # ... (other toolkit definitions omitted)

# Operator definitions: Units executing related actions, typically corresponding to a task phase
# Each Operator executes its `actions` using a `Reasoner` (usually configured at the Expert level).
# This `Reasoner` is typically an LLM-driven module responsible for understanding `instruction`,
# planning and invoking `tools` declared in `actions`, and generating final responses or decisions per `output_schema`.
# An Operator's `actions` can be sequential or parallel.
#
# Operator execution context includes:
# 1. Job details (goal, context)
# 2. Retrieved Knowledge from KnowledgeBaseService
# 3. FileDescriptor from FileService/MessageService for accessing file content
# 4. Preceding Operator/Expert outputs (WorkflowMessage)
# 5. Possible `lesson` (feedback from subsequent Experts guiding current Operator behavior)
operators:
  # Graph modeling operator example
  - &analysis_operator # Operator anchor
    instruction: | # LLM instructions describing its role, tasks, and notes
      You are a professional document analysis expert focused on extracting key info to build knowledge graphs.
      You need to understand document content. Note: analyzed documents may be subsets, requiring inference of the global context from local details.
    output_schema: | # Defines output format/structure, typically YAML/JSON
      **domain**: Document domain description aiding subsequent modeling
      **concepts**: Identified key concepts, each with name, description, importance
        *Example:*
          ```yaml
          concepts:
            - concept: "Person"
              description: "People mentioned in the document"
              importance: "High"
          ```
      # ... (other output fields)
    actions: # Actions invoked sequentially or selectively
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

  # ... (other operator definitions omitted, similar in format)

# Expert definitions: Higher-level abstractions representing specialized agents
# Each Expert includes a profile, reasoner configuration, and workflow
# Workflow consists of one or more Operators. Experts use their configured `reasoner` to drive `Operator` execution in `workflow`.
#
# Workflow mechanics:
# 1. Operator orchestration: `workflow` Operators form an execution graph (Operator Graph).
#    Experts execute Operators per this graph's structure and dependencies.
# 2. Message passing: Operators and Experts communicate via `WorkflowMessage` objects carrying data, state, and possible errors.
# 3. Evaluation: Workflows may include an `EvalOperator` assessing progress or output quality at key nodes, influencing subsequent flows.
experts:
  - profile: # Expert profile info
      name: "Design Expert" # Expert name
      desc: | # Detailed description in third person
        He is a knowledge graph modeling (schema) expert.
        His task is designing graph schemas per specific data needs, clearly defining vertex/edge types, properties, and relationships. He creates/updates schemas in graph data.
        He only creates or modifies data structures (schemas) for specific graph database instances.
        His output provides clear schema definitions for subsequent data imports. **He does not handle specific data (CRUD) or answer general questions about graph database products/technologies.**
    reasoner: # Expert's reasoner configuration, used by its workflow Operators
      actor_name: "Design Expert" # Actor name
      thinker_name: "Design Expert" # Thinker name (if reasoner.type is DUAL)
    workflow: # Expert's task execution workflow, one or more Operator lists
      - [*analysis_operator, *concept_modeling_operator] # This workflow includes two Operators (assuming concept_modeling_operator is defined)

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

  # ... (other expert definitions omitted, similar in format)

# Leader configuration: Responsible for task decomposition and coordination
# Leader mechanics:
# 1. JobGraph management: When a Leader executes, it transforms the original task into a subtask graph (JobGraph), a DAG defining subtasks (SubJob) and dependencies.
# 2. Dynamic scheduling: Leader schedules and executes JobGraph:
#    - Parallel processing: Independent or dependency-satisfied subtasks are scheduled in parallel.
#    - Expert feedback handling: Leader adjusts JobGraph execution based on Expert feedback (via WorkflowMessage), e.g.:
#      - `INPUT_DATA_ERROR`: May trigger re-planning/execution of related precursor tasks.
#      - `JOB_TOO_COMPLICATED_ERROR`: Expert deems subtask too complex; Leader treats it as a new original task for further decomposition.
leader:
  actions: # Leader-executable actions, typically for task decomposition and status queries
    - *query_system_status_action # Assuming defined
    - *job_decomposition_action # Assuming defined

# KnowledgeBase configuration (can be empty)
knowledgebase: {}

# Memory module configuration (can be empty)
memory: {}

# Environment variable configuration (can be empty)
env: {}
```

## 4. System Environment Configuration

Chat2Graph manages environment variables through the `SystemEnv` class, providing a unified configuration access interface. This design allows the system to retrieve configuration values from multiple sources with priority-based overrides.

The environment variable configuration primarily includes: large language model and embedding model invocation parameters, database configuration, knowledge base configuration, default generation language for large models, and system runtime parameters. Developers can quickly adjust system parameters by modifying the `.env` file or setting environment variables (you can search globally for corresponding environment variables and examine the source code to gain deeper insights into each parameter's functionality).

The priority order for environment variable assignment is: `.env` file configuration > OS environment variables > system default values. When the system starts, `SystemEnv` automatically loads configurations from the `.env` file (once only) and merges them with OS environment variables and predefined default values. Each environment variable has explicit type definitions and default values, with automatic type conversion and validation (supported types include: `bool`, `str`, `int`, `float`, and custom enum types such as `WorkflowPlatformType`, `ModelPlatformType`, etc.).

Additionally, the environment variable configuration management employs lazy loading and caching mechanisms. Environment variable values are parsed and cached upon first access, with subsequent accesses retrieving directly from the cache. The system also supports runtime dynamic modification of configuration values, facilitating debugging and testing.

### 4.1. Model Compatibility Notes

Chat2Graph supports all large language models and embedding models compatible with the OpenAI API standard, including but not limited to:

**Supported Large Language Models**:

- Google Gemini series (Gemini 2.0 Flash, Gemini 2.5 Flash, Gemini 2.5 Pro, etc. Must select versions [Compatible with OpenAI Interface](https://ai.google.dev/gemini-api/docs/openai))
- OpenAI series (GPT-4o, o3-mini, etc.)
- Anthropic Claude series (Claude Opus 4, Claude Sonnet 4, Claude Sonnet 3.7, Claude Sonnet 3.5, etc. Must select versions [Compatible with OpenAI Interface](https://docs.anthropic.com/en/api/openai-sdk))
- Alibaba Tongyi Qianwen series (Qwen-3)
- Zhipu GLM series
- DeepSeek series
- Other model services supporting OpenAI API format

**Supported Embedding Models**:

- OpenAI Embedding series (text-embedding-3-small, text-embedding-3-large, etc.)
- Gemini Embedding series (select versions compatible with OpenAI interface)
- Alibaba Tongyi Qianwen embedding models (text-embedding-v3, etc.)
- Other models compatible with OpenAI Embeddings API, such as SiliconFlow, etc.

Simply configure the corresponding model name, API endpoint, and key in the `.env` file to use them. The system automatically handles API call details for different model providers. Based on testing experience, we recommend using models like Gemini 2.0 Flash, Gemini 2.5 Flash, or o3-mini for better inference performance and cost-effectiveness.

## 5. Examples

* YAML Configuration Construction: `test/example/agentic_service/load_service_by_yaml.py`
  * Default System YAML Configuration Example: `app/core/sdk/chat2graph.yml`
* SDK Programmatic Construction: `test/example/agentic_service/load_service_by_sdk.py`
* Sessionless Service Execution: `test/example/agentic_service/run_agentic_service_without_session.py`
* Session-based Service Execution: `test/example/agentic_service/run_agentic_service_with_session.py`