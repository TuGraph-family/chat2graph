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
# It defines the application's basic information, available tools, actions the agent can perform,
# Operators for executing specific tasks, Experts with specialized skills, and their workflows.

# Application Basic Information Configuration
app:
  name: "Chat2Graph"  # Application name, e.g., "Chat2Graph"
  desc: "An Agentic System on a Graph Database." # Application description, briefly explaining its function
  version: "0.0.1" # Application version number

# Plugin Configuration
plugin:
  workflow_platform: "DBGPT" # Specifies the platform the workflow depends on, e.g., "DBGPT".

# Reasoner Configuration
reasoner:
  type: "DUAL" # Specifies the type of reasoner, e.g., "MONO" (single reasoner) or "DUAL" (dual reasoner, typically includes an Actor and a Thinker, offering stronger reasoning capabilities at the cost of longer inference time, suitable for highly complex tasks)

# Tools Definition: Defines a series of atomic functional modules that the Agent can use.
# Each tool defines an anchor with "&tool_alias" for easy reference in actions using "*tool_alias".

# 1. Core Philosophy of Tools
#    - Functional Positioning: Tools are the bridge for the Agent to interact with the external world or execute deterministic tasks. They encapsulate operations that Large Language Models (LLMs)
#      cannot perform directly, such as file I/O, API calls, database queries, and precise calculations.
#    - Non-creative Tasks: Tools execute predefined, deterministic logic implemented in code. They are not suitable for open-ended creative tasks
#      (like writing an article or generating complex business code). Such tasks should be handled directly by the LLM (i.e., the Reasoner), while tools can assist in
#      processing the results (e.g., saving the generated code to a file).
# 2. Tool Types and Implementation
#    This configuration file focuses on the orchestration and use of tools, not their underlying development. The system primarily supports the following two tool types:
#    - LOCAL_TOOL: A local tool executed directly via function calls in the Agent's Python environment.
#      `module_path` points to the Python module containing the tool's implementation.
#    - MCP (A Client connected to an MCP Server): An inter-process communication tool used to interact with separate external processes or services.
#      This is crucial for integrating complex tools that are not implemented in Python or require an isolated environment (like Playwright for browser automation). It generally requires an external MCP Server to be available.
#      Its behavior is defined by `mcp_transport_config`:
#        - transport_type: The communication protocol, such as "STDIO" (Standard Input/Output), "SSE" (Server-Sent Events), "WebSocket", etc.
#        - command / args: When type is "STDIO", these are used to start the external process.
#        - url: When type is "SSE" or "WebSocket", this is the network address for connecting to the external service.

tools:
  # Example 1: Document Reader Tool
  - &document_reader_tool
    name: "DocumentReader"
    type: "LOCAL_TOOL" # (Optional) Defaults to a local tool
    module_path: "app.plugin.resource.common.document_reader" # The tool's Python module path

  # Example 2: File Writer Tool
  - &file_writer_tool
    name: "FileWriter"
    type: "LOCAL_TOOL"
    module_path: "app.plugin.resource.common.file_writer"

  # Example 3: Database Schema Getter Tool (Domain-Specific)
  - &schema_getter_tool
    name: "SchemaGetter"
    type: "LOCAL_TOOL"
    module_path: "app.plugin.neo4j.resource.data_importation"

  # Example 4: Browser Automation Tool (Launched via STDIO)
  - &browser_tool_stdio
    name: "BrowserUsing"
    type: "MCP"
    mcp_transport_config:
      transport_type: "STDIO" # Communicate with the child process via standard I/O
      command: "npx" # Command to start the child process
      args: ["@playwright/mcp@latest"] # Arguments passed to the command

  # Example 5: Browser Automation Tool (Connected to a service via SSE)
  - &browser_tool_sse
    name: "BrowserUsing"
    type: "MCP"
    mcp_transport_config:
      transport_type: "SSE" # Connect to a running service via Server-Sent Events
      url: "http://localhost:8931" # The address the browser service is listening on
  # ... More tools of different types can be defined here as needed.

# Action Definition: Defines the specific actions an Agent can take when performing a task.
# Each action includes a name, description (desc), and the tools required to complete the action.
actions:
  # Graph Modeling Related Action Example
  - &content_understanding_action # Action anchor
    name: "content_understanding" # Unique name for the action
    desc: "Understands the main content and structure of a document by reading and annotating it (requires calling one or more tools)." # Detailed description of the action, explaining its function and purpose
    tools: # List of tools this action may depend on during execution
      - *document_reader_tool # Reference to the previously defined document_reader_tool

  - &deep_recognition_action
    name: "deep_recognition"
    desc: | # Multi-line description detailing the action's execution logic and thinking dimensions
      Identifies and analyzes key concepts and terms in text, classifies concepts, discovers relationship patterns and interaction modes between them, and establishes a hierarchical structure.
      Example thinking dimensions:
      1. Entity Type Definition
         - Think about and define entity types from temporal, spatial, social, cultural, physical, and other dimensions.
         - Establish a hierarchical system for entity types.
      2. Relationship Type Design
         - Define relationship types between entities, including direct, derived, and potential relationships.
    # tools: (If this action directly calls tools, list them here)

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
      - *document_reader_tool # Re-using document_reader_tool assuming it can read any text file like markdown or HTML

  # ... (Other action definitions are omitted here, format is similar to the above)

# Toolkit Definition: Combines related actions into toolkits for use by a specific Operator or Expert.
# Each toolkit is a list of actions.
toolkit:
  - [*content_understanding_action, *deep_recognition_action] # First toolkit, containing two actions
  - [ # Web Development Toolkit Example
      *generate_html_code_action,
      *save_generated_code_action,
      *review_generated_html_action
    ]
  # - [ # Second toolkit example
  #     *entity_type_definition_action, # Assumed to be defined
  #     *relation_type_definition_action, # Assumed to be defined
  #     *schema_design_and_import_action, # Assumed to be defined
  #   ]
  # ... (Other toolkit definitions are omitted here)

# Operator Definition: An Operator is a unit that executes a series of related actions, typically corresponding to a phase of a task.
# When executing its defined `actions`, each Operator relies on a `Reasoner` (usually configured uniformly at the Expert level or specified as needed).
# This `Reasoner` is typically a module driven by a Large Language Model (LLM), responsible for understanding the `instruction`,
# planning and invoking the `tools` declared in the `actions`, and generating the final response or decision according to the `output_schema`.
# The `actions` of each Operator can be a list, and these behaviors can be executed sequentially or in parallel.
# Each Operator includes an instruction, an output_schema, and the actions it can execute.
#
# Supplementary Explanation of Operator Execution Mechanism:
# 1. Execution Context: When an Operator executes, it receives a rich context, including:
#    - Detailed information about the current `Job` (e.g., `goal`, `context`).
#    - Relevant `Knowledge` retrieved from the `KnowledgeBaseService`.
#    - `FileDescriptor`s provided through the `FileService` and `MessageService` for accessing relevant file content.
#    - The output from a preceding Operator or Expert (`WorkflowMessage`).
#    - A possible `lesson` (feedback from a subsequent Expert to guide the current Operator's behavior).
# 2. Toolkit Interaction Configuration: The Operator retrieves tools from the Toolkit that are related to the Actions in the Operator Config, enabling the Operator-driven Reasoner to call these tools.
operators:
  # Graph Modeling Operator Example
  - &analysis_operator # Operator anchor
    instruction: | # Instruction for the LLM, describing its role, task, and points to note
      You are a professional document analysis expert, focused on extracting key information from documents to lay a solid foundation for building a knowledge graph.
      You need to understand the document's content. Please note that the document you are analyzing may be a subset of a complete collection, requiring you to infer the overall situation from local details.
    output_schema: | # Defines the format and structure of the Operator's output, usually in YAML or JSON format description
      **domain**: A description of the document's domain, to assist in subsequent modeling and data extraction.
      **concepts**: A list of identified key concepts, each including a name, description, and importance.
        *Example:*
          ```yaml
          concepts:
            - concept: "Person"
              description: "Refers to the people mentioned in the document."
              importance: "High"
          ```
      # ... (other output fields)
    actions: # List of actions called sequentially or selectively when this Operator executes
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

  # ... (Other operator definitions are omitted here, format is similar to the above)

# Expert Definition: An Expert is a higher-level abstraction, representing an agent with specific capabilities.
# Each Expert includes a profile, reasoner configuration, and a workflow.
# The workflow consists of one or more Operators. The Expert drives the execution of the Operators in its `workflow` using its configured `reasoner`.
#
# Workflow Mechanism Explanation:
# 1. Operator Orchestration: The list of Operators defined in the `workflow` is not just a simple sequence; they can form an execution graph (Operator Graph).
#    The Expert executes the Operators according to the structure and dependencies of this graph.
# 2. Information Passing: Data and state are passed between Operators, and between an Expert and its internal Operators, via `WorkflowMessage` objects.
#    This message object carries the output, status, and possible error information for each step.
# 3. Evaluation Mechanism: The execution of a Workflow may include a special `EvalOperator`. This evaluation operator is responsible for assessing the progress or quality of the output at key nodes or at the final stage of the Workflow. Its evaluation results can influence the subsequent flow.
experts:
  - profile: # The expert's profile information
      name: "Design Expert" # The expert's name
      desc: | # A detailed description of the expert, explaining its capabilities, task scope, and limitations. Please use the third person.
        He is an expert in knowledge graph modeling (schema).
        His task is to design the graph's Schema based on specific data requirements, clearly defining the types, properties, and relationships of Vertices and Edges. He also creates/updates the Schema in the graph database.
        He only creates or modifies the data structure (Schema) for a specific graph database instance.
        His output is a clear Schema definition for subsequent data importation. **He does not handle specific data (CRUD) himself, nor does he ever answer general introductory or consulting questions about graph database products or technologies.**
    reasoner: # The reasoner configuration used by this expert, which will be used by the Operators in its workflow
      actor_name: "Design Expert" # Specifies the Actor's name
      thinker_name: "Design Expert" # Specifies the Thinker's name (if reasoner.type is DUAL)
    workflow: # The workflow this expert follows when performing tasks, consisting of one or more lists of Operators
      - [*analysis_operator, *concept_modeling_operator] # This workflow contains two Operators (assuming concept_modeling_operator is defined)

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

  # ... (Other expert definitions are omitted here, format is similar to the above)

# Leader Configuration: Responsible for task decomposition and coordination.
# Leader Mechanism Explanation:
# 1. JobGraph Management: When the Leader executes, it doesn't just decompose the task.
#    Instead, it transforms the original task into a subgraph of tasks (JobGraph), which is a Directed Acyclic Graph (DAG) defining the sub-tasks (SubJobs) and their dependencies.
# 2. Dynamic Scheduling and Execution: The Leader is responsible for scheduling and executing the JobGraph:
#    - Parallel Processing: Sub-tasks with no dependencies or whose dependencies are met are scheduled and executed in parallel.
#    - Handling Expert Feedback: The Leader dynamically adjusts the JobGraph's execution based on the status returned by an Expert after executing a sub-task (via WorkflowMessage). For example:
#      - `INPUT_DATA_ERROR`: May cause related preceding tasks to be replanned or re-executed.
#      - `JOB_TOO_COMPLICATED_ERROR`: The Expert deems the sub-task too complex. The Leader will treat this sub-task as a new original task and decompose it further, deepening the JobGraph.
leader:
  actions: # Actions the Leader can perform, typically for task decomposition and status queries
    - *query_system_status_action # Assumed to be defined
    - *job_decomposition_action # Assumed to be defined

# Knowledge Base Configuration (can be left empty)
knowledgebase: {}

# Memory Module Configuration (can be left empty)
memory: {}

# Environment Variables Configuration (can be left empty)
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