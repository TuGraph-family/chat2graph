---
title: Agent
---

## 1. Introduction

The Agent module serves as the core execution unit of Chat2Graph, responsible for receiving tasks (`Job`), performing specific operations, and returning results. In a multi-agent system, agents undertake the central responsibility of task processing, coordinating the collaborative work of various components through their built-in workflow mechanisms.

Each agent consists of three core components: Profile, Reasoner, and Workflow. The `Profile` defines the agent's identity and capability scope, the `Reasoner` provides a large language model-based reasoning engine (natural language processing capabilities), while the `Workflow` orchestrates the specific task execution process.

```python
@dataclass
class AgentConfig:
    profile: Profile
    reasoner: Reasoner
    workflow: Workflow
```

The Chat2Graph system features two special types of agents: Leader and Expert.

- The **Leader** agent specializes in task decomposition and coordination. When receiving complex tasks, it breaks them down into subtasks and assigns them to appropriate Experts based on each subtask's characteristics.
- **Expert** agents focus on domain-specific task processing, with each Expert having clearly defined professional boundaries and execution responsibilities.

## 2. Design

### 2.1. Profile

The agent Profile serves as its identity and capability definition, containing the agent's **name** and **description**:

- **ame**: For experts, the profile name serves as an identifier recognized by the leader for task assignment and result tracing, such as querying which Jobs have been assigned to a particular expert.
- **description**: Details the agent's professional capabilities, task scope, and operational constraints, helping the Leader better assign tasks based on expert configuration information.

The description section of an agent's Profile should emphasize clarity and professionalism. When defining it, developers must explicitly specify:
- The types of tasks it can handle
- Required preconditions for execution
- Clear boundaries of responsibilities it should not undertake

We recommend developers **follow these guidelines for more effective agent configuration**:

- **Clearly Defined Capability Boundaries**: The Profile description should explicitly list the agent's core competencies and operational limits. For example, a Design Expert's description should clearly state "it can only create or modify data structures (Schema) for specific graph database instances" and "it does not handle actual data operations (CRUD)." Such clear boundaries prevent ambiguity during task assignment.

- **Declaration of Preconditions and Dependencies**: Agents with specific prerequisites must declare them in their Profile. For instance, an Extraction Expert might require that "the graph schema must already exist with defined node labels and edge labels," ensuring the Leader can properly evaluate task feasibility during assignment.

- **Precise Delineation of Responsibilities**: Use negative descriptions to clarify responsibilities the agent should not undertake. For example, stating "will never answer general inquiries about graph database products or technologies" helps the Leader avoid assigning inappropriate tasks.

- **Concrete Output Expectations**: The Profile should specify the agent's typical output format, such as "it will output summaries or status reports of data import processes," which aids in subsequent workflow design and task chain construction.

### 2.2. Reasoner

The [Reasoner](./reasoner.md) serves as the agent's large language model reasoning core, invoking LLMs to perform reasoning tasks. During workflow execution, the Reasoner handles:
- Understanding task instructions
- Generating responses
- Calling external tools
- Performing complex reasoning

### 2.3. Workflow

The [Workflow](./workflow.md) is the agent's core task execution mechanism, defining the complete processing pipeline from task receipt to result output. Composed of a series of Operators, each handles specific processing stages, with data transferred between them via WorkflowMessage to form an ordered processing chain.

When executing tasks through workflows, agents create corresponding Job objects, with `JobService` tracking task status. Job objects contain task objectives, contextual information, and various intermediate results generated during execution.

## 3. Implementation

### 3.1. Leader

The [Leader](./leader.md) agent acts as the coordinator in the agent system, responsible for analyzing, decomposing, and scheduling complex tasks. Its main responsibilities include:

- **Job Planning**: Breaking down complex tasks into executable subtasks.
- **Job Assignment**: Allocating subtasks to appropriate Expert agents based on their characteristics and required resources.
- **Job Execution**: Ensuring subtask execution, monitoring progress, and adjusting strategies as needed.

### 3.2. Expert

Expert agents are specialized executors in the system, handling domain-specific tasks. Each has clearly defined professional boundaries and execution responsibilities, enabling efficient completion of assigned subtasks.

Beyond predefined Expert configurations, Chat2Graph will eventually support **automated Expert generation**. The Leader will analyze task requirements to dynamically create Experts with corresponding Profiles and Workflows. This dynamic expansion capability allows the system to handle novel scenarios beyond preset configurations, enabling truly scalable multi-agent collaboration networks—even multi-agent communities—through intelligent Agent generation and configuration.

## 4. API

Core Agent API design:

| Method Signature | Description |
|:-----------------|:------------|
| `get_id() -> str` | Returns the agent's unique identifier |
| `get_profile() -> Profile` | Retrieves the agent's configuration information |
| `execute(agent_message: AgentMessage, retry_count: int = 0) -> Any` | Abstract task execution method implemented by subclasses |
| `save_output_agent_message(job: Job, workflow_message: WorkflowMessage, lesson: Optional[str] = None) -> AgentMessage` | Saves execution results as a message object with persistence |

Note: Agent execution follows a message-driven pattern, receiving task requests via AgentMessage and generating WorkflowMessages containing results and metadata upon completion. The system also incorporates an Artifact management mechanism for handling various data resources produced during execution, including graph data and textual content.