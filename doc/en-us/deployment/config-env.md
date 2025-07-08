---
title: Configure .env
---

## 1. LLM Configuration

### 1.1. LiteLLM Configuration Rules (Recommended)

> LiteLLM is a unified LLM API interface supporting 100+ model providers.

#### How it works

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Chat2Graph     │───▶│    LiteLLM      │───▶│  Model Provider │
│  Application    │    │    Router       │    │  (OpenAI/etc)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                            │
                            ▼
                       Routes by model prefix
```

#### Model Name Format

Format: `provider/model_name` or `provider/organization/model_name`

**Examples (model names may change):**

- **OpenAI Official**: `openai/gpt-4o`, `openai/gpt-3.5-turbo`
- **Google Official**: `gemini/gemini-2.5-pro`, `gemini/gemini-2.5-flash`
- **Anthropic Official**: `anthropic/claude-sonnet-4-20250514`
- **Third-party or Self-hosted**: `openai/deepseek-ai/DeepSeek-V3`, `openai/custom-model-name`

#### API Endpoint Routing Logic

1. **LLM_ENDPOINT** must always have a value
2. For official APIs, use the provider's official endpoint URL
3. For third-party platforms, use the platform's endpoint URL
4. LiteLLM automatically handles API format differences between providers
5. API key is set through **LLM_APIKEY**, or use environment variables (e.g., `OPENAI_API_KEY`)

#### Configuration Examples

**Scenario 1: OpenAI Official API**

```env
LLM_NAME=openai/gpt-4o
LLM_ENDPOINT=https://api.openai.com/v1
LLM_APIKEY=
```

**Scenario 2: Google Official API**

```env
LLM_NAME=gemini/gemini-2.5-pro
# LiteLLM handles the endpoint automatically, but set for consistency
LLM_ENDPOINT=https://generativelanguage.googleapis.com/v1beta
LLM_APIKEY=
```

**Scenario 3: Anthropic Official API**

```env
LLM_NAME=anthropic/claude-sonnet-4-20250514
LLM_ENDPOINT=https://api.anthropic.com
LLM_APIKEY=
```

**Scenario 4: Third-party Platform or Self-hosted Service**

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

#### Detailed Request Flow

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

#### Common Troubleshooting

| Issue | Solution |
|-------|----------|
| Incorrect model name format | Check if prefix is correct (`openai/`, `anthropic/`, `gemini/`, etc) |
| API key error | Confirm key format and permissions, check if expired |
| Endpoint unreachable | Check network connection and URL format, confirm endpoint is correct |
| Model not found | Confirm model name is available at provider, check spelling |
| Timeout error | Adjust network timeout settings, check provider service status |
| Quota limit | Check API quota and billing status |

**Code implementation reference:** `lite_llm_client.py`

### 1.2. AISuite Configuration Rules (No longer updated)

> **Note:** AISuite project hasn't been updated for months, recommend using LiteLLM

#### How it works:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Chat2Graph     │───▶│    AISuite      │───▶│  Model Provider │
│  Application    │    │    Client       │    │  (OpenAI/etc)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                            │
                            ▼
                       Hardcoded config routing
```

#### Model Name Format

Format: `provider:model_name` (Note: use colon, not slash)

**Examples:**

- **OpenAI**: `openai:gpt-4o`, `openai:gpt-3.5-turbo`
- **Anthropic**: `anthropic:claude-sonnet-4-20250514`
- **Google**: `google:gemini-pro`
- **Custom deployment**: `openai:custom-model-name`
- **SiliconFlow (Third-party Platform)**: `openai:deepseek-ai/DeepSeek-V3`

#### Configuration Limitations

- Does not support dynamic configuration via environment variables, poor flexibility
- Can only support new providers or endpoints through code modification

**Code implementation reference:** `aisuite_client.py`

## 2. Embedding Model Configuration

The embedding model uses an independent configuration system, not dependent on `MODEL_PLATFORM_TYPE`.

#### Configuration Rules

- Uses OpenAI compatible format by default, so no `openai/` prefix needed
- Supports custom endpoints and API keys

#### Example Configuration

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
