---
title: 配置 .env
---

## 1. LLM 配置

### 1.1. LiteLLM 配置规则（推荐）

> LiteLLM 是一个统一的 LLM API 接口，支持 100+ 模型提供商。

#### 工作原理

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Chat2Graph     │───▶│    LiteLLM      │───▶│  Model Provider │
│  Application    │    │    Router       │    │  (OpenAI/etc)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                            │
                            ▼
                       Routes by model prefix
```

#### 模型名称格式

格式：`provider/model_name` 或 `provider/organization/model_name`

**示例（模型名称可能会变化）：**

- **OpenAI 官方**: `openai/gpt-4o`, `openai/gpt-3.5-turbo`
- **Google 官方**: `gemini/gemini-2.5-pro`, `gemini/gemini-2.5-flash`
- **Anthropic 官方**: `anthropic/claude-sonnet-4-20250514`
- **第三方平台或自托管**: `openai/deepseek-ai/DeepSeek-V3`, `openai/custom-model-name`

#### API 端点路由逻辑

1. **LLM_ENDPOINT** 必须始终有值
2. 对于官方 API，使用提供商的官方端点 URL
3. 对于第三方平台，使用平台的端点 URL
4. LiteLLM 自动处理提供商之间的 API 格式差异
5. API 密钥通过 **LLM_APIKEY** 设置，或使用环境变量（例如 `OPENAI_API_KEY`）

#### 配置示例

**场景 1: OpenAI 官方 API**

```env
LLM_NAME=openai/gpt-4o
LLM_ENDPOINT=https://api.openai.com/v1
LLM_APIKEY=
```

**场景 2: Google 官方 API**

```env
LLM_NAME=gemini/gemini-2.5-pro
LLM_ENDPOINT=  # do not set the endpoint for Gemini, LiteLLM will use the default
LLM_APIKEY=
```

**场景 3: Anthropic 官方 API**

```env
LLM_NAME=anthropic/claude-sonnet-4-20250514
LLM_ENDPOINT=https://api.anthropic.com
LLM_APIKEY=sk-ant-xxx
```

**场景 4: 第三方平台或自托管服务**

```env
# Example 1: SiliconFlow
# https://www.siliconflow.com/models#llm#llm
LLM_NAME=openai/deepseek-ai/DeepSeek-V3 # optional openai/Qwen/Qwen3-32B
LLM_ENDPOINT=https://api.siliconflow.cn/v1
LLM_APIKEY=
MAX_TOKENS=8192
MAX_COMPLETION_TOKENS=8192

# Example 2: BaiLian
# https://bailian.console.aliyun.com
LLM_NAME=openai/deepseek-v3 # optional openai/qwen-max
LLM_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_APIKEY=
MAX_TOKENS=8192
MAX_COMPLETION_TOKENS=8192

# Example 3: Self-hosted OpenAI Compatible Service
LLM_NAME=openai/your-model-name
LLM_ENDPOINT=http://localhost:8000/v1
LLM_APIKEY=
```

#### 详细请求流程

```
Chat2Graph Request
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LiteLLM Router                             │
│                                                                 │
│  1. Parse model name prefix                                     │
│     └─ "openai/" → OpenAI adapter                               │
│     └─ "anthropic/" → Anthropic adapter                         │
│     └─ "gemini/" → Google adapter                               │
│                                                                 │
│  2. Select corresponding provider adapter                       │
│     └─ Set correct API format and parameters                    │
│                                                                 │
│  3. Handle API key & endpoint                                   │
│     └─ LLM_ENDPOINT must always have a value                    │
│     └─ Use official endpoint for official APIs                  │
│     └─ Use custom endpoint for third-party/self-hosted          │
│                                                                 │
│  4. Format request parameters                                   │
│     └─ Convert to target provider's API format                  │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   OpenAI API    │  │ Anthropic API   │  │  Google API     │
│                 │  │                 │  │                 │
│Official/3rd/Self│  │   Official      │  │   Official      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

#### 常见问题排查

| 问题 | 解决方案 |
|-------|----------|
| 模型名称格式不正确 | 检查前缀是否正确（`openai/`, `anthropic/`, `gemini/` 等） |
| API 密钥错误 | 确认密钥格式和权限，检查是否过期 |
| 端点无法访问 | 检查网络连接和 URL 格式，确认端点正确 |
| 模型未找到 | 确认模型名称在提供商处可用，检查拼写 |
| 超时错误 | 调整网络超时设置，检查提供商服务状态 |
| 配额限制 | 检查 API 配额和计费状态 |

**代码实现参考：** `lite_llm_client.py`

## 2. 嵌入模型配置

嵌入模型使用独立的配置系统，不依赖于 `MODEL_PLATFORM_TYPE`。

#### 配置规则

- 默认使用 OpenAI 兼容格式，因此不需要 `openai/` 前缀
- 支持自定义端点和 API 密钥

#### 配置示例

```env
# OpenAI https://platform.openai.com/docs/api-reference
EMBEDDING_MODEL_NAME=embedding-ada-002
EMBEDDING_MODEL_ENDPOINT=https://api.openai.com/v1/embeddings
EMBEDDING_MODEL_APIKEY=

# SiliconFlow https://www.siliconflow.com/models#llm
EMBEDDING_MODEL_NAME=Qwen/Qwen3-Embedding-4B
EMBEDDING_MODEL_ENDPOINT=https://api.siliconflow.cn/v1/embeddings
EMBEDDING_MODEL_APIKEY=

# BaiLian https://bailian.console.aliyun.com
EMBEDDING_MODEL_NAME=text-embedding-v4
EMBEDDING_MODEL_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings
EMBEDDING_MODEL_APIKEY=

# Self-Hosted OpenAI Compatible Service
EMBEDDING_MODEL_NAME=your-embedding-model
EMBEDDING_MODEL_ENDPOINT=http://localhost:8000/v1/embeddings
EMBEDDING_MODEL_APIKEY=
```

## 3. 记忆（MemFuse）配置

MemFuse 是一个可选的内存后端，以插件形式提供。当你需要在进程外持久化记忆时可启用它。

> 想深入了解记忆架构？请参考[记忆系统指南](../principle/memory.md)。

```env
ENABLE_MEMFUSE=true
PRINT_MEMORY_LOG=true
MEMFUSE_BASE_URL=http://localhost:8765
MEMFUSE_API_KEY=
MEMFUSE_TIMEOUT=30
MEMFUSE_RETRY_COUNT=3
MEMFUSE_RETRIEVAL_TOP_K=5
MEMFUSE_MAX_CONTENT_LENGTH=10000
```

### 3.1 注意事项

- `ENABLE_MEMFUSE` 控制 `MemoryService` 是否实例化 MemFuse 记忆，关闭时仅使用进程内的 `BuiltinMemory`。
- `MEMFUSE_BASE_URL` 必须指向 MemFuse 服务；若不可访问会在初始化阶段直接报错。
- `MEMFUSE_API_KEY` 根据部署环境决定是否需要填写。
- `MEMFUSE_RETRIEVAL_TOP_K` 和 `MEMFUSE_MAX_CONTENT_LENGTH` 决定检索和写入的上下文规模。
