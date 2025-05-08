# Model Service - 模块技术文档

## 1. 模块概览 (Module Overview)

* **核心职责与定位**:
  * 在 Chat2Graph 中，本模块作为与大型语言模型 (LLM) 交互的核心接口和实现层。
  * 提供统一的 API，封装不同 LLM 平台（如 DB-GPT, AiSuite）的调用细节。
* **解决的关键问题/核心价值**:
  * **LLM 交互抽象**: 屏蔽底层不同 LLM API 的差异性。
  * **功能调用集成**: 解析 LLM 输出中的函数/工具调用请求，并执行相应的工具。
  * **平台解耦**: 使上层模块（如 Reasoner）能够以统一的方式与不同 LLM 后端交互。
* **主要功能点**:
  * 定义 `ModelService` 抽象基类接口。
  * 提供针对特定 LLM 平台的具体实现 (`DbgptLlmClient`, `AiSuiteLlmClient`)。
  * 处理 `ModelMessage` 与特定 LLM API 格式的转换。
  * 基于系统提示 (System Prompt) 和消息历史生成 LLM 响应。
  * 解析 LLM 响应中的函数调用指令 (例如，通过 `<function_call>` 标签)。
  * 执行请求的函数/工具（同步或异步）。
  * 通过类型提示自动注入服务依赖项到被调用的函数中。
  * 格式化函数调用结果，并可能将其包含在后续发往 LLM 的消息中。
  * 提供工厂类 (`ModelServiceFactory`) 以根据配置创建具体的 `ModelService` 实例。

## 2. 模块架构与设计 (Module Architecture & Design)

* **核心组件**:
  * `ModelService` (ABC): 定义了与 LLM 交互的统一接口 (`generate`, `call_function`)。
  * `DbgptLlmClient`, `AiSuiteLlmClient`: `ModelService` 的具体实现，分别对接 DB-GPT 和 AiSuite 平台。
  * `ModelServiceFactory`: 工厂类，根据系统配置 (`SystemEnv.MODEL_PLATFORM_TYPE`) 创建并返回相应的 LLM Client 实例。
* **函数调用机制**:
  * 依赖 `app.core.common.util.parse_jsons` 和 `<function_call>...</function_call>` 标签格式从 LLM 输出中提取函数调用请求。
  * 使用 `inspect` 模块分析函数签名，以支持 `app.core.reasoner.injection_mapping` 中定义的服务依赖注入。

## 3. SDK Wrapper 参考: Model Service (SDK Wrapper Reference: Model Service)

注意：Model Service 主要通过工厂模式和其定义的接口在框架内部被使用，**没有**像 Agent 或 Workflow 那样独立的 `ModelServiceWrapper` 类。

## 4. 核心方法说明 (Core Method Description)

### 4.1. `ModelServiceFactory.create()`

* **描述**: 创建并返回一个特定 LLM 平台 (`ModelPlatformType`) 的 `ModelService` 实例。这是获取 Model Service 对象的主要入口点。

### 4.2. `ModelService.generate()`

* **描述**: 异步方法，接收系统提示、消息历史 (`List[ModelMessage]`) 和可选的工具列表 (`List[Tool]`)，调用底层 LLM 生成响应，并返回一个包含 LLM 输出和可能的函数调用结果的 `ModelMessage` 对象。

### 4.3. `ModelService.call_function()`

* **描述**: 异步方法，内部由 `generate` 调用。接收工具列表和 LLM 的文本响应，解析出 `<function_call>` 请求，查找并执行相应的工具函数（处理同步/异步及依赖注入），返回包含执行结果或错误的 `FunctionCallResult` 列表。

## 5. 使用方法与示例 (Usage & Examples)

### 5.1. 示例场景: 基本 LLM 响应生成

* **描述**: 此示例展示了如何使用 `ModelServiceFactory` 创建一个 `ModelService` 实例，并调用其 `generate` 方法来获取 LLM 的文本响应。
* **代码参考**: 请查看位于 `test/example/run_model_service.py` 的示例代码。

### 5.2. 示例场景: LLM 驱动的函数调用

* **描述**: 此示例演示了 `ModelService` 如何解析 LLM 响应中包含的 `<function_call>` 指令，并自动执行相应的同步或异步工具函数。
* **代码参考**: 请查看位于 `test/example/run_function_calling.py` 的示例代码。
