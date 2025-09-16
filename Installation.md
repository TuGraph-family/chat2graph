# 安装与配置指南 (Installation & Configuration Guide)

## 环境准备 (Prerequisites)

在开始安装 Chat2Graph 之前，请确保您的系统满足以下要求：

### 系统要求 (System Requirements)
- **操作系统**: Linux、macOS 或 Windows (推荐 Linux/macOS)
- **Python**: 3.10 - 3.11 (不支持 3.12+)
- **内存**: 至少 4GB RAM (推荐 8GB+)
- **存储**: 至少 2GB 可用磁盘空间

### 必需的软件依赖 (Required Dependencies)

#### 1. Python 和包管理器
```bash
# 检查 Python 版本
python --version  # 应该是 3.10.x 或 3.11.x

# 安装 Poetry (推荐的依赖管理工具)
curl -sSL https://install.python-poetry.org | python3 -
```

#### 2. 数据库依赖
```bash
# Neo4j (图数据库) - 可选，使用 Docker 安装
docker run -d \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest

# 或者安装本地版本
# 参考: https://neo4j.com/docs/operations-manual/current/installation/
```

## 安装步骤 (Installation Steps)

### 1. 克隆项目代码
```bash
# 从 GitHub 克隆项目
git clone https://github.com/TuGraph-family/chat2graph.git
cd chat2graph
```

### 2. 安装项目依赖
```bash
# 使用 Poetry 安装所有依赖
poetry install

# 安装开发依赖（用于开发和测试）
poetry install --with dev

# 安装 Web 服务依赖
poetry install --with service

# 安装测试依赖
poetry install --with test

# 安装 DB-GPT 集成依赖（可选）
poetry install --with db-gpt
```

### 3. 环境配置
```bash
# 复制环境变量模板文件
cp .env.template .env

# 编辑配置文件
vim .env  # 或使用您喜欢的编辑器
```

## 项目启动 (Running the Project)

### 本地开发环境启动

#### 方式一：使用脚本启动（推荐）
```bash
# 启动所有服务（包括 MCP 服务器）
bash bin/start.sh

# 查看服务状态
bash bin/status.sh

# 停止服务
bash bin/stop.sh

# 重启服务
bash bin/restart.sh
```

#### 方式二：手动启动
```bash
# 进入项目环境
poetry shell

# 启动主服务
python app/server/bootstrap.py

# 启动 MCP 服务器（新终端）
bash bin/start_mcp_server.sh
```

### 验证安装
```bash
# 检查服务是否正常运行
curl http://localhost:5000/health

# 查看日志
tail -f ~/.chat2graph/logs/server.log
```

## 关键配置项说明 (Key Configurations)

### LLM 模型配置 (.env 文件)
```env
# 模型平台类型 - 选择 "LITELLM" 或 "AISUITE"
MODEL_PLATFORM_TYPE="LITELLM"

# 大语言模型配置
LLM_NAME=openai/deepseek-ai/DeepSeek-V3
LLM_ENDPOINT=https://api.siliconflow.cn/v1
LLM_APIKEY=your_api_key_here

# 嵌入模型配置 (Embedding Model)
EMBEDDING_MODEL_NAME=Qwen/Qwen3-Embedding-4B
EMBEDDING_MODEL_ENDPOINT=https://api.siliconflow.cn/v1/embeddings
EMBEDDING_MODEL_APIKEY=your_embedding_api_key_here

# 模型参数
TEMPERATURE=0           # 生成随机性 (0-1)
MAX_TOKENS=8192        # 最大令牌数
PRINT_REASONER_MESSAGES=1  # 是否打印推理消息
```

### 记忆服务配置 (Memory Service Configuration)
```env
# MemFuse 集成配置
MEMORY_ENABLED=true                    # 启用记忆服务
MEMORY_RETRIEVAL_ENABLED=true         # 启用记忆检索
MEMORY_ASYNC_WRITE=true               # 异步写入记忆

# MemFuse 服务设置
MEMFUSE_BASE_URL=http://localhost:8001  # MemFuse 服务地址
MEMFUSE_TIMEOUT=30.0                   # 超时设置
MEMFUSE_RETRY_COUNT=3                  # 重试次数

# 记忆性能配置
MEMORY_MAX_CONTENT_LENGTH=10000        # 最大内容长度
MEMORY_CACHE_TTL=300                  # 缓存生存时间
MEMORY_RETRIEVAL_TOP_K=5              # 检索返回数量
MEMORY_MAX_MEMORIES_IN_CONTEXT=3      # 上下文中最大记忆数量
```

### 系统配置
```env
# 语言设置
LANGUAGE=en-US  # 或 zh-CN

# 日志配置
MEMORY_LOG_LEVEL=INFO          # 日志级别
MEMORY_LOG_operations=true     # 记录操作日志
```

## 推荐的模型服务商 (Recommended Model Providers)

基于测试结果（考虑幻觉、推理速度、成本等因素），我们推荐以下模型：

### 首选推荐
1. **DeepSeek V3** (通过 SiliconFlow 部署)
   - 优势：访问便捷、API 价格低廉
   - 配置：已在 `.env.template` 中预配置

2. **Gemini 2.0 Flash / 2.5 Flash**
   - 优势：推理速度快、性价比高
   
3. **OpenAI o3-mini** 或更大参数的 LLM
   - 优势：推理能力强、稳定性好

### API 密钥获取
- **SiliconFlow**: https://cloud.siliconflow.cn/
- **OpenAI**: https://platform.openai.com/
- **Google AI**: https://makersuite.google.com/

## ⚠️ 注意事项 (Important Notes)

### 常见安装问题

#### 1. Python 版本问题
```bash
# 如果系统有多个 Python 版本，确保使用正确版本
pyenv install 3.11.5  # 使用 pyenv 管理 Python 版本
pyenv local 3.11.5
```

#### 2. Poetry 安装问题
```bash
# 如果 Poetry 安装失败，尝试使用 pip
pip install poetry

# 或者使用 conda
conda install poetry
```

#### 3. 依赖冲突问题
```bash
# 清理缓存重新安装
poetry cache clear pypi --all
poetry install --no-cache
```

#### 4. Neo4j 连接问题
```bash
# 检查 Neo4j 是否正常运行
docker ps | grep neo4j

# 测试连接
curl http://localhost:7474/
```

### 性能优化建议

1. **内存优化**
   - 如果内存有限，可以降低 `MAX_TOKENS` 参数
   - 调整 `MEMORY_CACHE_TTL` 减少缓存占用

2. **网络优化**
   - 使用国内 API 服务商减少延迟
   - 调整 `MEMFUSE_TIMEOUT` 适应网络环境

3. **并发优化**
   - 根据硬件配置调整工作进程数量
   - 配置适当的连接池大小

### 故障排除

#### 服务启动失败
```bash
# 查看详细错误日志
tail -f ~/.chat2graph/logs/server.log

# 检查端口占用
netstat -tlnp | grep :5000

# 清理残留进程
bash bin/stop.sh
pkill -f "app/server/bootstrap.py"
```

#### API 调用失败
```bash
# 检查 API 密钥配置
grep -E "(API|KEY)" .env

# 测试 API 连接
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.siliconflow.cn/v1/models
```

### 生产环境部署

在生产环境中，建议：

1. **使用 Docker 容器化部署**
2. **配置反向代理 (Nginx)**
3. **设置日志轮转**
4. **配置监控和告警**
5. **使用环境变量管理敏感配置**

详细的生产环境部署指南请参考：[部署文档](doc/en-us/deployment/overview.md)

---

## 下一步

安装完成后，您可以：

1. 查看 [架构总览](Architecture/Overview.md) 了解系统架构
2. 阅读 [代码精粹分析](Code-Analysis/Highlights.md) 学习优秀实践
3. 参考 [测试指南](Testing/Guide.md) 运行测试用例
4. 访问 Web 界面开始使用：http://localhost:5000