# Reasoner - 模块技术文档

## 1. 模块概览 (Module Overview)

- **核心职责与定位**: Reasoner 模块是 Chat2Graph 中与大语言模型 (LLM) 交互的核心。它负责处理提示词、执行推理任务、并支持工具/函数调用。
- **解决的关键问题/核心价值**:
  - 提供统一接口与不同 LLM 进行交互。
  - 封装 LLM API 调用的复杂性。
  - 使 Agent 能够利用 LLM 进行复杂思考和任务执行。
  - 支持结构化输出和函数调用能力。
- **主要功能点快速列表**:
  - LLM 交互 (请求发送与响应接收)。
  - 提示词管理与构建。
  - 函数/工具调用支持。
  - 提供两种核心推理器实现：`MonoModelReasoner` 和 `DualModelReasoner`。

## 2. 模块架构与设计 (Module Architecture & Design)

- **核心组件**:
  - `Reasoner` (抽象基类): 定义推理器的标准接口。
  - `MonoModelReasoner`: 使用单一 LLM 完成所有推理步骤。
  - `DualModelReasoner`: 使用两个协同工作的 LLM（通常一个主模型（Thinker）负责复杂推理和规划，一个辅助模型（Actor）负责如工具调用或特定子任务处理）。
  - `ReasonerMemory`: (位于 `app/core/memory/reasoner_memory.py`) 用于管理和提供推理过程中的记忆。
  - `ModelService`: 封装与具体 LLM 服务端点交互的逻辑。
  - `ModelServiceFactory`: 用于创建 `ModelService` 实例。

    ![Dual Reasoner](../../en/img/dual-reasoner.png)

- **`MonoModelReasoner` vs `DualModelReasoner` 详解**:
  - **`MonoModelReasoner` (单模型推理器)**:
    - **工作方式**: 依赖单个 LLM 实例来理解用户指令、进行思考、选择工具（如果需要）、并生成最终回复或执行动作。所有阶段的智能均由这一个模型提供。
    - **优点**:
      - **配置简单**: 设置和管理相对直接，只需配置一个模型。
      - **逻辑一致性**: 由于所有处理步骤都由同一模型完成，其推理的链路更短。
    - **缺点**:
      - **灵活性较低**: 对于需要更强的推理能力或者一些复杂组合的任务（例如，强大的通用理解能力 + 复杂的工具使用能力），单一模型可能无法很好地完成任务。
      - **成本/性能权衡**: 为了和 `DualModelReasoner` 能力持平，`MonoModelReasoner` 就需要更加大参数量的单一模型。这是一个取舍。
    - **适用场景**: 任务复杂度相对单一，或者所选模型本身在各个方面都表现优异且满足成本效益。

  - **`DualModelReasoner` (双模型推理器)**:
    - **工作方式**: 通常采用一个“思考型”（Thinker）和一个“执行型”（Actor）协同工作。
      - **主模型（Thinker）**: 通常是能力更强、理解和规划能力更出色的 LLM，负责理解复杂的用户意图、分解任务、制定计划、以及在需要时决定调用哪个工具或子任务。
      - **副模型（Actor）**: 是一个在特定方面（遵循指令进行格式化输出、执行特定类型的函数调用、快速思考回答）更高效的 Actor LLM。主模型可以将具体的、定义清晰的、步骤性的任务或工具调用请求传递给副模型执行。
    - **优点**:
      - **任务专业化**: 允许针对特定子任务使用专门优化的角色 Prompt（通过角色扮演），提高整体效果。例如，一个模型擅长代码生成 Actor，另一个擅长自然语言对话 Thinker。
      - **增强的工具使用**: 副模型可以专门用于处理工具调用的请求和响应格式化，使得主模型可以更专注于核心的推理和规划。
    - **缺点**:
      - **配置复杂性**: 需要调用两个模型（Thinker、Actor），其 Prompt 需要特定的设置。
      - **推理延迟**: 两个模型之间的“对话”会导致推理的时间过长。
    - **适用场景**: 复杂任务，其中包含需要两个模型合作的任务。例如，需要强大规划能力同时也需要频繁、快速执行工具调用的场景。

  - **性能差距总结**:
    - `MonoModelReasoner` 的性能完全取决于所选的单一 LLM。
    - `DualModelReasoner` 的潜力在于通过分配任务给不同角色的模型，以达到整体更优的性能。例如，主模型处理复杂逻辑，副模型快速处理格式固定的工具调用。然而，如果模型间的协调不当，也可能引入额外开销或者信息损耗，比如一个模型误解另一个模型的指示。实际性能表现需根据具体任务、所选模型及实现细节进行评估。

## 3. SDK Wrapper 参考: Reasoner (SDK Wrapper Reference: Reasoner)

### 3.1. `ReasonerWrapper`

- **描述**: 为 `Reasoner` 模块（包括 `MonoModelReasoner` 和 `DualModelReasoner`）提供了一个便捷的SDK接口，便于推理器的创建、配置和调用。
- **主要方法或属性简介**:
  - `build(reasoner_type: ReasonerType)`: 根据指定的 `reasoner_type` 初始化并构建相应的推理器实例。
  - `reasoner` (属性): 获取当前配置的 `Reasoner` 实例。如果推理器未设置，则会引发错误。
  - `get_memory(job: Job)`: 获取与特定 `Job` 关联的 `ReasonerMemory` 实例，用于管理推理过程中的记忆和上下文。
  - `get_messages(job: Job)`: 获取与特定 `Job` 关联的完整消息列表。
  - `get_message_by_index(job: Job, index: int)`: 根据索引获取特定 `Job` 关联的某条消息。

## 4. 使用方法与示例 (Usage & Examples)

### 4.1. 示例场景: 使用单模型推理器进行函数调用

- **描述**: 此示例演示了如何配置和使用 `MonoModelReasoner` 来与支持函数调用的 LLM 进行交互，并执行外部工具。
- **代码参考**: 请查看位于 `test/example/run_mono_reasoner_with_func_calling.py` 的示例代码。

### 4.2. 示例场景: 使用双模型推理器进行函数调用

- **描述**: 此示例展示了如何配置和运用 `DualModelReasoner`，可能利用一个模型进行规划，另一个模型辅助执行函数调用。
- **代码参考**: 请查看位于 `test/example/run_dual_reasoner_with_func_calling.py` 的示例代码。

### 4.3. 示例场景: 通用推理器调用（不依赖特定函数调用）

- **描述**: 此示例可能演示了 `Reasoner` 的基本调用流程，用于生成文本或进行不涉及外部工具调用的推理。
- **代码参考**: 请查看位于 `test/example/run_reasoner_without_func_calling.py` 的示例代码。
