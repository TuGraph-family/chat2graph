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
- **Anthropic Official**: `anthropic/claude-3-5-sonnet-20240620`
- **Google Official**: `gemini/gemini-2.5-pro`, `gemini/gemini-2.0-flash`
- **Custom OpenAI Compatible**: `openai/custom-model-name`
- **Third-party Platform**: `openai/deepseek-ai/DeepSeek-V3`

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
LLM_APIKEY=sk-xxx
```

**Scenario 2: Third-party Platform (e.g., SiliconFlow)**

```env
LLM_NAME=openai/deepseek-ai/DeepSeek-V3
LLM_ENDPOINT=https://api.siliconflow.cn/v1
LLM_APIKEY=sk-xxx
```

**Scenario 3: Anthropic Official API**

```env
LLM_NAME=anthropic/claude-3-5-sonnet-20240620
LLM_ENDPOINT=https://api.anthropic.com
LLM_APIKEY=sk-ant-xxx
```

**Scenario 4: Self-hosted OpenAI Compatible Service**

```env
LLM_NAME=openai/your-model-name
LLM_ENDPOINT=http://localhost:8000/v1
LLM_APIKEY=your-api-key
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
- **Anthropic**: `anthropic:claude-3-5-sonnet-20240620`
- **Google**: `google:gemini-pro`
- **Custom deployment**: `openai:custom-model-name`
- **Third-party platform**: `openai:deepseek-ai/DeepSeek-V3`

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
EMBEDDING_MODEL_NAME=Qwen/Qwen3-Embedding-4B
EMBEDDING_MODEL_ENDPOINT=https://api.siliconflow.cn/v1/embeddings
EMBEDDING_MODEL_APIKEY=
```