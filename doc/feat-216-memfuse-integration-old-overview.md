# `feat/216-memfuse-integration-old` Overview

This branch captures an earlier attempt to integrate MemFuse into Chat2Graph. While it is no longer functional, the intended architecture aligns with the current design and is preserved here for reference.

## System Architecture Flow

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

## Data Flow Diagram

### Reasoner Memory Enhancement Flow

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

### Operator Experience Learning Flow

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

### MemFuse Integration Notes

- **Memory Retrieval** uses `query` with no additional arguments.
- **Experience Retrieval** uses `query` with `metadata: {"task": "<some_task_name>"}`.
- **Reasoning Logs** use `add` with no extra metadata.
- **Operator Logs** use `add` with `metadata: {"task": "<some_task_name>"}`.

