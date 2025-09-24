---
title: Memory System
---

## 1. Introduction

The Memory system is the core component of Chat2Graph responsible for information storage, retrieval, and management. Through its multi-level memory system design, it defines the process of refining raw data into high-level wisdom insights, including memory storage, information evaluation, experience extraction, and insight generation. This provides persistent learning and adaptive capabilities for the entire Chat2Graph system, enhancing its overall intelligence.

> The functionality of the memory system is still under continuous development. This section focuses on the design philosophy, and we welcome interested contributors to join the community in building it together.

## 2. Design

### 2.1. Layered Memory Architecture

Inspired by the [DIKW](https://en.wikipedia.org/wiki/DIKW_pyramid) pyramid model, Chat2Graph abstracts memory into four hierarchical levels:

| Level | Name          | Description                                                                 | Storage Content                                      | Typical Use Cases                                     |
|:-----:|:--------------|:----------------------------------------------------------------------------|:-----------------------------------------------------|:------------------------------------------------------|
| **L0 (D)** | **History**   | Message History Layer                                                      | Reasoning messages, tool invocation records, system logs, etc. | Full traceability, debugging, basic retrieval         |
| **L1 (I)** | **Evaluation**| Process Evaluation Layer                                                   | Evaluation results, performance metrics, state classifications, etc. | Quality control, error diagnosis, pattern recognition |
| **L2 (K)** | **Lesson**    | Experience Summary Layer                                                   | Experience rules, best practices, domain knowledge, etc. | Decision support, strategy optimization, skill transfer |
| **L3 (W)** | **Insight**   | High-level Insight Layer                                        | High-level decision patterns, strategic insights, etc. | High-dimensional decision-making, user preferences, global optimization |

### 2.2. Hierarchical Knowledge Management

The content accessed at different memory levels varies significantly. For simplicity, we uniformly refer to it as "knowledge."

![memory-architecture](../../asset/image/memory-arch.png)

Traditional memory systems typically employ a single storage architecture, primarily addressing knowledge production and consumption. In contrast, the layered memory system introduces multi-level knowledge abstraction, managing knowledge at a finer granularity. Overall, it encompasses three aspects:

* **Knowledge Refinement**: Raw knowledge undergoes progressive processing, analysis, abstraction, and compression to form higher-level knowledge, expanding knowledge production capabilities.
* **Knowledge Drilling**: While using high-level knowledge, lower-level knowledge can be drilled down as needed, ensuring that reasoning contexts are both broad and detailed, strengthening knowledge consumption.
* **Knowledge Expansion**: Refers to the construction and recall of associations between knowledge at the same level, enriching the knowledge context through specific methods. A typical example is RAG (Retrieval-Augmented Generation).

## 3. Memory System Extension

Broadly speaking, the layered memory design can better accommodate the concepts of Knowledge Base and Environment. In other words, from a technical implementation perspective, the architectures of the memory system, knowledge base, and environment can be unified.

### 3.1. Knowledge Base

Generally, a knowledge base is viewed as a "closed" storage repository for external knowledge. To improve the quality of knowledge recall, most RAG frameworks focus on improving peripheral technologies around the knowledge base, such as query rewriting, document splitting, re-ranking, etc., while overlooking improvements to the knowledge content itself. GraphRAG can be seen as a relatively early attempt in this direction. The introduction of a layered memory system provides an "open" solution for fine-grained knowledge management.

Thus, in a sense, **"The Knowledge Base is a Specialized Expression of the Memory System in Vertical Domain Knowledge."** Currently, Chat2Graph initially implements RAG as the form of the knowledge base. Once the layered memory architecture is refined, the knowledge base will be further integrated. For details on using the knowledge base, refer to the [Knowledge Base](../cookbook/knowledgebase.md) documentation.

### 3.2. Environment

The environment refers to the external space with which an Agent interacts during execution. The agent can perceive environmental changes and influence environmental states through tool operations. Essentially, **"The Environment can be Viewed as 'External Memory at the Current Moment,' while Memory is 'Snapshots of the Environment at Historical Moments.'"** This homogeneity allows the environment to seamlessly integrate into the layered memory model. Environmental information perceived by the Agent through tools is essentially raw data at the L0 level, which can be further refined into higher-level insights (L1~L3). Conversely, accumulated experiences in the memory system directly effect global consensus and high-level insights in the environment. 

Using "tools" as a bridge, the memory system and environmental state can be deeply interconnected, constructing a mapping relationship between the agent's "mental world" and the external environment's "physical world"—the world knowledge model.

## 4. Implementation

We introduces the MemFuse service as the memory backend for Chat2Graph. A MemoryService singleton mediates all interactions with MemFuse and is invoked through pre- and post- hooks around reasoning and operator execution.

### System Architecture Flow

```mermaid
graph TB
    subgraph "Chat2Graph Enhanced System"
        A[User Request] --> B[Leader Agent]
        B --> C[Task Decomposition]
        C --> D[Enhanced Reasoner]
        C --> E[Enhanced Operator]

        subgraph "Memory Enhancement Layer"
            F[Pre-Reasoning Hook]
            G[Post-Reasoning Hook]
            H[Pre-Execution Hook]
            I[Post-Execution Hook]
            J[MemoryService Singleton]
        end

        D --> F
        F --> K[Memory Retrieval]
        K --> L[Context Enhancement]
        L --> M[Original Reasoning]
        M --> G
        G --> N[Memory Write]

        E --> H
        H --> O[Experience Retrieval]
        O --> P[Context Enhancement]
        P --> Q[Original Execution]
        Q --> I
        I --> R[Experience Write]
    end

    subgraph "MemFuse External Service"
        S[M1: Episodic Memory]
        T[M2: Semantic Memory]
        U[M3: Procedural Memory]
        V[Query API]
        W[Messages API]
    end

    J --> W
    J --> V
    K --> V
    O --> V
    N --> W
    R --> W

    style D fill:#e1f5fe
    style E fill:#e8f5e8
    style J fill:#fff3e0
    style S fill:#f3e5f5
    style T fill:#f3e5f5
    style U fill:#f3e5f5
```

### Data Flow Diagram

#### Reasoner Memory Enhancement Flow

```mermaid
sequenceDiagram
    participant T as Task
    participant ER as EnhancedReasoner
    participant H as Hook Manager
    participant MS as MemoryService
    participant MF as MemFuse API
    participant BR as Base Reasoner

    T->>ER: infer(task)
    ER->>H: execute_pre_reasoning_hooks()
    H->>MS: retrieve_relevant_memories()
    MS->>MF: POST /api/v1/users/{user_id}/query
    MF-->>MS: historical memories
    MS-->>H: RetrievalResult[]
    H-->>ER: enhanced context
    ER->>ER: enhance_task_context()
    ER->>BR: infer(enhanced_task)
    BR-->>ER: reasoning_result
    ER->>H: execute_post_reasoning_hooks()
    H->>MS: write_reasoning_log()
    MS->>MF: POST /sessions/{session_id}/messages
    MF-->>MS: success
    ER-->>T: reasoning_result
```

#### Operator Experience Learning Flow

```mermaid
sequenceDiagram
    participant J as Job
    participant EO as EnhancedOperator
    participant H as Hook Manager
    participant MS as MemoryService
    participant MF as MemFuse API
    participant BO as Base Operator

    J->>EO: execute(job)
    EO->>H: execute_pre_execution_hooks()
    H->>MS: retrieve_relevant_memories()
    MS->>MF: POST /api/v1/users/{user_id}/query?tag=m3
    MF-->>MS: execution experiences
    MS-->>H: RetrievalResult[]
    H-->>EO: enhanced context
    EO->>EO: enhance_job_context()
    EO->>BO: execute(enhanced_job)
    BO-->>EO: execution_result
    EO->>H: execute_post_execution_hooks()
    H->>MS: write_operator_log()
    MS->>MF: POST /sessions/{session_id}/messages?tag=m3
    MF-->>MS: success
    EO-->>J: execution_result
```