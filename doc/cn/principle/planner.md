# Planner 模块

## 1. 规划器的介绍

规划器（Planner）并不是一个严格意义上的模块。实际上，`Leader` 作为一个特殊的 Agent， 管理着所有的任务生命周期和 Expert 的存在。但是在多代理系统（Multi-Agent System）中，任务规划是一个避不开的话题，并且这个模块又相对复杂。因此，本章节专门来讲解该规划器（`Planner`）。

## 2. 子任务字段以及 `JobGraph`

Chat2Graph 明确了子任务包含的字段（`JOB_DECOMPOSITION_OUTPUT_SCHEMA`）：

| 字段                  | 描述                                                                                                |
| :-------------------- | :-------------------------------------------------------------------------------------------------- |
| `goal`                | 目标，必须精确反映用户最新请求。                                                                            |
| `context`             | 上下文，需包含对话历史摘要、用户反馈以及这些上下文如何塑造当前任务。                                                              |
| `completion_criteria` | 完成标准，需明确且可衡量，直接回应对话历史中突显的需求或修正。                                                                |
| `dependencies`        | 依赖关系，仅在生成多个子任务时定义，用于确定子任务之间的依赖关系，形成一张 `JobGraph`，由 `JobService` 负责管理。                               |
| `assigned_expert`     | 分配的专家名，制定该子任务由哪位专家完成。                                                                        |
| `thinking`            | 思考过程，要求 LLM 以第一人称解释生成该子任务的思考过程，包括其必要性、初步方法及关键考量。                                                          |

`JobGraph` 是一个有向无环图（DAG），表达了子任务之间的依赖关系：

<p align="center">
  <img src="../../en/img/job-graph.png" alt="job-graph" width="50%">
</p>

## 3. 规划器 prompt 分析

规划器的核心在于一个精心设计的 Prompt，即 `JOB_DECOMPOSITION_PROMPT`，它指导 `Leader` 将一个主任务（`Given Task`）分解为一系列可执行的子任务。

`Leader` 将首先结合对话历史与系统当前状态，来主动推断用户的真实意图和期望的下一个逻辑步骤。基于此推断，`Leader` 需确定完成该步骤所需的目标专家（`Expert`）及其行动。任务分解是其唯一输出，即使在信息不完整的情况下（例如用户提及忘记上传文件），也必须为相关专家制定子任务，并在子任务上下文中注明潜在问题。分解时，LLM 应力求最少的必要逻辑子任务，同时确保子任务的分配仅限于先前确定的专家。每个子任务需包含所有必要信息，保持角色中立，并严格限制在原始任务范围内。对于简单或仅需单一专家的任务，则应生成单个子任务。

## 4. 规划器机制

我们借助自动状态机来解释 `Job/SubJob` 与 `Agent` 之间的传递、转换机制。

`Leader` 在收到原始任务（`OriginalJob`）后，若无预设 `Expert`，则首先通过其内置的 `Workflow` 和 `Reasoner` 将其分解为一张子任务图（`JobGraph`）。这张图是一个有向无环图（DAG），其中节点代表子任务（`SubJob`），边代表子任务间的依赖关系。

- 如果原始任务已经预设了 `Expert`，那么 `Leader` 将会跳过任务拆解的过程，然后直接将该任务分配给预设的 `Expert`，同时 `JobGraph` 将只有一个节点———该原始任务。

随后，`Leader` 调用 `execute_job_graph` 方法来“执行”这张图：

1. **并行调度任务**：`Leader` 使用线程池并行调度无前置依赖或所有前置依赖已完成的子任务。它会持续监控任务状态，一旦任何某个子任务的所有前置任务完成，该子任务即被提交执行。
2. **Expert 处理任务**：每个子任务 `SubJob` 被分派给指定的 `Expert`。`Expert` 执行其内部工作流（`Workflow`）来处理子任务。

    ![job-asignment](../../en/img/job-asignment.png)

3. **状态机**：`Expert` 执行完毕后会返回一个 `WorkflowMessage`，其中包含 `workflow_status`，该状态决定了后续流程：
    - `SUCCESS`：子任务成功完成。`Leader` 会记录结果，并更新 `JobGraph` 的状态，进而可能触发后续依赖任务的执行。
    - `EXECUTION_ERROR`：`Expert` 执行过程中发生内部错误（如 API 请求失败）。`Leader` 会根据重试策略（`retry_count`）决定是否重试该 `Expert` 的执行。若达到最大重试次数，则该子任务及整个 `JobGraph` 可能会被标记为 `FAILED`。
    - `INPUT_DATA_ERROR`：`Expert` 判断输入数据有问题，无法继续执行。`Leader` 接收到此状态后，会将此子任务及其前置依赖任务重新加入待处理队列，并可能附带 `lesson`（经验教训）给前置任务的 `Expert`，以便修正输出。
    - `JOB_TOO_COMPLICATED_ERROR`：`Expert` 认为当前子任务过于复杂，无法独立完成。`Leader` 会将此子任务视为一个新的“原始任务”，再次调用任务分解逻辑，将其进一步细化为更小的子任务，并更新到 `JobGraph` 中。为防止无限分解，子任务设有生命周期（`life_cycle`）计数 —— 每一次任务分解，生命周期将会减少 1，直到 0 为止。

    ![state-machine](../../en/img/state-machine.png)

4. **完成与终止 `JobGraph`**：当 `JobGraph` 中的所有子任务都成功完成，整个原始任务即告完成。若任何关键子任务最终失败或整个图的执行被中断（例如，`Leader` 调用 `fail_job_graph` 或 `stop_job_graph`），则原始任务会相应地标记为 `FAILED` 或 `STOPPED`。

这种状态机确保了任务能够根据依赖关系进行并行处理，同时具备对执行过程中各类情况的适应性和纠错能力。此外，`JobGraph` 还支持中断（`stop_job_graph`）和恢复（`recover_original_job`）操作，使得在 `planner` 调度下的多智能体协作更加灵活和可控。

## 5. 案例场景

下图展示了一个规划器的案例场景：

![planner-case](../../en/img/planner-case.png)

## 6. API

### 6.1. Leader API

`Leader` Agent 负责任务的分解、调度和整体流程控制。

| 方法签名                                     | 描述                                                                                                                                                                                                                                                           |
| :--------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `execute(self, agent_message: AgentMessage, retry_count: int = 0) -> JobGraph` | 核心的任务分解方法。接收一个包含待处理任务（可能是原始任务或需要进一步分解的子任务）的 `AgentMessage`。如果任务已预设专家，则直接创建单节点 `JobGraph`；否则，调用其内部工作流 (`Workflow`) 和推理器 (`Reasoner`) 将任务分解为一张子任务图 (`JobGraph`)。此方法包含对分解结果的校验和基于 `lesson` 的重试逻辑。 |
| `execute_original_job(self, original_job: Job) -> None`          | 接收一个原始任务 (`OriginalJob`)。首先将其状态更新为 `RUNNING`，然后调用 `execute` 方法将其分解为子任务图，并将此图存入 `JobService`。最后，调用 `execute_job_graph` 来执行这张图。                                                                                                                            |
| `execute_job_graph(self, original_job_id: str) -> None`          | 执行指定 `original_job_id` 对应的子任务图 (`JobGraph`)。它使用 `ThreadPoolExecutor` 并行调度无依赖或所有前置依赖已完成的子任务。此方法处理子任务执行后的不同 `WorkflowStatus`（如 `SUCCESS`, `INPUT_DATA_ERROR`, `JOB_TOO_COMPLICATED_ERROR`），并据此更新任务图状态或重新调度任务。                 |
| `stop_job_graph(self, job_id: str, error_info: str) -> None`     | 停止与给定 `job_id` (可以是原始任务 ID 或子任务 ID) 相关的整个任务图。将原始任务及所有未完成（且无最终结果）的子任务状态标记为 `STOPPED`，并记录错误信息作为系统消息。正在运行的任务不会被强制中断，但其完成后状态也会被相应更新。                                                                                             |
| `fail_job_graph(self, job_id: str, error_info: str) -> None`     | 标记指定的 `job_id` 对应的任务结果为 `FAILED`（如果尚无最终结果），然后调用 `stop_job_graph` 来停止相关的整个任务图，并将其他未完成任务标记为 `STOPPED`。                                                                                                                                                              |
| `recover_original_job(self, original_job_id: str) -> None`       | 恢复一个先前被标记为 `STOPPED` 的原始任务。如果该原始任务没有子任务（即未被分解），则将其状态重置为 `CREATED` 并重新调用 `execute_original_job`。如果已有子任务，则将原始任务状态设为 `RUNNING`，并将所有状态为 `STOPPED` 的子任务重置为 `CREATED`，然后重新调用 `execute_job_graph`。 |
| `state(self) -> LeaderState` (property)                          | 获取 `Leader` 的状态对象 (`LeaderState`)。该状态对象管理 `Leader` 可用的 `Expert` 列表等运行时状态信息。                                                                                                                                                                              |

### 6.2. Expert API

`Expert` Agent 负责执行具体的子任务。

| 方法签名                                      | 描述                                                                                                                                                                                             |
| :--------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `execute(self, agent_message: AgentMessage, retry_count: int = 0) -> AgentMessage` | 执行分配给该 `Expert` 的子任务 (`SubJob`)。首先检查任务是否已有最终结果，若无则将任务状态更新为 `RUNNING`。然后调用其内部工作流 (`Workflow`) 处理任务。根据工作流返回的 `WorkflowStatus`（如 `SUCCESS`, `EXECUTION_ERROR`, `INPUT_DATA_ERROR`, `JOB_TOO_COMPLICATED_ERROR`）进行相应处理，包括保存结果、重试（`retry_count`）或准备特定的 `AgentMessage` 返回给 `Leader`。 |
