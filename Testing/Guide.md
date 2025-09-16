# 测试指南 (Testing Guide)

## 测试架构 (Testing Architecture)

Chat2Graph 采用**分层测试架构 (Layered Testing Architecture)**，包含单元测试、集成测试和基准测试三个层次，确保系统各个组件的正确性和性能表现。

### 测试目录结构 (Test Directory Structure)

```
test/
├── __init__.py
├── unit/                           # 单元测试
│   ├── test_leader_execution.py    # Leader 智能体执行测试
│   ├── test_dual_model_reasoner.py # 双模型推理器测试
│   ├── test_mono_model_reasoner.py # 单模型推理器测试
│   ├── test_memory_service.py      # 记忆服务测试
│   ├── test_memory_hooks.py        # 记忆钩子测试
│   ├── test_workflow.py           # 工作流测试
│   ├── test_job_decomposition.py  # 作业分解测试
│   ├── test_toolkit.py           # 工具包测试
│   ├── test_operator.py          # 操作算子测试
│   └── wrapper/                  # SDK 包装器测试
│       ├── test_session_wrapper.py
│       ├── test_workflow_wrapper.py
│       └── test_operator_wrapper.py
├── benchmark/                    # 基准测试
│   └── gaia/                    # GAIA 基准测试
│       ├── run_hf_gaia_test.py  # HuggingFace GAIA 测试
│       └── gaia_agents.yml      # 智能体配置
└── example/                     # 示例和集成测试
    ├── agentic_service/         # 智能体服务示例
    ├── domain_expert/          # 领域专家示例
    └── graph_agent/            # 图智能体示例
```

## 测试类型与工具 (Test Types & Tools)

### 1. 单元测试 (Unit Tests)

#### 测试框架
- **Pytest**: 主要测试框架，支持异步测试
- **Unittest.mock**: 模拟外部依赖
- **Pytest-asyncio**: 异步测试支持
- **Pytest-cov**: 测试覆盖率统计

#### 配置文件 - `pyproject.toml:89-96`
```toml
[tool.pytest.ini_options]
testpaths = ["test"]
python_files = ["test_*.py"]
addopts = "-v"
asyncio_mode = "auto"  # 自动异步模式
markers = [
    "asyncio: mark test as async"
]
```

### 2. 集成测试 (Integration Tests)

通过 `test/example/` 目录下的示例程序验证系统集成：

#### 智能体服务集成测试
- **加载服务测试**: `load_service_by_sdk.py`, `load_service_by_yaml.py`
- **会话管理测试**: `run_agentic_service_with_session.py`
- **无会话执行测试**: `run_agentic_service_without_session.py`

#### 领域专家测试
- **浏览器使用专家**: `broswer_use_expert.yml`

#### 图智能体测试
- **数据导入**: `data_importation.yml`
- **图分析**: `graph_analysis.yml`
- **图建模**: `graph_modeling.yml`
- **图查询**: `graph_query.yml`
- **问答系统**: `question_answering.yml`

### 3. 基准测试 (Benchmark Tests)

#### GAIA 基准测试
**GAIA (General AI Assistant benchmark)** 是评估 AI 助手能力的标准基准。

- **数据集下载**: `download_hf_gaia_dataset.py`
- **测试执行**: `run_hf_gaia_test.py`
- **智能体配置**: `gaia_agents.yml`

## 核心测试用例解读 (Core Test Cases)

### 1. Leader 智能体执行测试 (Leader Execution Test)

#### 测试文件: `test/unit/test_leader_execution.py`

```python
class TestAgentOperator(Operator):
    """测试用的操作算子 - 模拟不同类型的任务"""
    
    async def execute(self, reasoner, job, workflow_messages=None, 
                     previous_expert_outputs=None, lesson=None):
        
        # Job1: 生成数字序列
        if self._config.id == "gen":
            result = "\n" + job.context.strip()
            return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)
        
        # Job2: 数字乘以2
        elif self._config.id == "mult":
            numbers = [int(x) for x in previous_expert_outputs[-1].scratchpad.strip().split()]
            result = " ".join(str(x * 2) for x in numbers)
            return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)
        
        # Job3: 数字加10
        elif self._config.id == "add":
            numbers = [int(x) for x in previous_expert_outputs[-1].scratchpad.strip().split()]
            result = " ".join(str(x + 10) for x in numbers)
            return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)
```

**测试目标**:
- **任务分解**: 验证 Leader 能够正确分解复杂任务
- **依赖管理**: 确保任务间的依赖关系得到正确处理
- **结果聚合**: 测试多个专家结果的聚合逻辑
- **并发执行**: 验证独立任务的并行执行能力

### 2. 双模型推理器测试 (Dual Model Reasoner Test)

#### 测试文件: `test/unit/test_dual_model_reasoner.py`

```python
@pytest.fixture
async def mock_reasoner() -> DualModelReasoner:
    """创建带模拟响应的双模型推理器"""
    reasoner = DualModelReasoner()
    
    # 模拟 Actor 响应
    actor_response = ModelMessage(
        source_type=MessageSourceType.ACTOR,
        payload="<shallow_thinking>\n测试中\n</shallow_thinking>\n<action>\n继续执行\n</action>",
        job_id="test_job_id",
        step=1,
    )
    
    # 模拟 Thinker 响应
    thinker_response = ModelMessage(
        source_type=MessageSourceType.THINKER,
        payload="<deep_thinking>\n深度分析\n</deep_thinking>\n<deliverable>\n最终结果\n</deliverable>",
        job_id="test_job_id", 
        step=2,
    )
    
    # 设置模拟响应
    reasoner._thinker_model_service = AsyncMock(return_value=thinker_response)
    reasoner._actor_model_service = AsyncMock(return_value=actor_response)
    
    return reasoner
```

**测试要点**:
- **Actor-Thinker 协作**: 验证双模型间的协作流程
- **迭代推理**: 测试多轮推理的逻辑
- **响应解析**: 确保模型响应的正确解析
- **异步处理**: 验证异步推理的正确性

### 3. 记忆服务测试 (Memory Service Test)

#### 测试文件: `test/unit/test_memory_service.py`

```python
@pytest.fixture
def mock_memory_service():
    """模拟记忆服务"""
    service = MagicMock()
    service.create_memory = AsyncMock(return_value={"id": "test-memory-id"})
    service.query_memories = AsyncMock(return_value=[
        {"content": "相关记忆1", "relevance": 0.9},
        {"content": "相关记忆2", "relevance": 0.8}
    ])
    return service

@pytest.fixture  
def memory_hook_manager(mock_memory_service):
    """记忆钩子管理器"""
    return MemoryHookManager(mock_memory_service)

async def test_pre_execution_hook(memory_hook_manager):
    """测试执行前钩子"""
    # 测试记忆创建和上下文增强
    
async def test_post_execution_hook(memory_hook_manager):
    """测试执行后钩子""" 
    # 测试记忆存储和反馈处理
```

**测试覆盖**:
- **记忆创建**: 验证记忆实体的创建流程
- **记忆检索**: 测试相关记忆的查询和排序
- **钩子机制**: 确保前后置钩子的正确执行
- **异常处理**: 验证记忆服务不可用时的降级处理

### 4. 工作流测试 (Workflow Test)

#### 测试文件: `test/unit/test_workflow.py`

```python
class MockOperator(Operator):
    """模拟操作算子"""
    
    def __init__(self, operator_id: str, delay: float = 0.1):
        super().__init__(operator_id)
        self.delay = delay
        self.execution_count = 0
    
    async def execute(self, **kwargs) -> WorkflowMessage:
        """模拟执行过程"""
        await asyncio.sleep(self.delay)  # 模拟执行时间
        self.execution_count += 1
        
        return WorkflowMessage(
            payload={"result": f"Operator {self.id} executed"},
            job_id=kwargs.get("job", {}).get("id", "unknown")
        )

async def test_workflow_execution_order():
    """测试工作流执行顺序"""
    # 验证操作按正确的依赖顺序执行
    
async def test_workflow_parallel_execution():
    """测试并行执行"""
    # 验证独立操作的并发执行
    
async def test_workflow_error_handling():
    """测试错误处理"""
    # 验证单个操作失败时的处理机制
```

## 如何运行测试 (How to Run Tests)

### 1. 运行全部测试
```bash
# 进入项目根目录
cd chat2graph

# 激活虚拟环境
poetry shell

# 运行所有测试
pytest

# 运行测试并显示覆盖率
pytest --cov=app --cov-report=html --cov-report=term
```

### 2. 运行特定测试类别

#### 单元测试
```bash
# 运行所有单元测试
pytest test/unit/

# 运行特定模块的测试
pytest test/unit/test_leader_execution.py

# 运行特定测试方法
pytest test/unit/test_dual_model_reasoner.py::test_dual_model_reasoning
```

#### 基准测试
```bash
# 运行 GAIA 基准测试
python test/benchmark/gaia/run_hf_gaia_test.py

# 下载 GAIA 数据集
python test/benchmark/gaia/download_hf_gaia_dataset.py
```

#### 集成测试（示例）
```bash
# 运行智能体服务示例
python test/example/agentic_service/run_agentic_service_with_session.py

# 运行图智能体示例
python test/example/graph_agent/run_data_importation.py
```

### 3. 测试选项和标记

#### 异步测试
```bash
# 只运行异步测试
pytest -m asyncio

# 运行特定的异步测试
pytest test/unit/test_dual_model_reasoner.py -m asyncio
```

#### 详细输出
```bash
# 详细输出模式
pytest -v

# 显示测试执行时间
pytest --durations=10

# 显示最慢的测试
pytest --durations=0
```

#### 并行执行
```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 并行运行测试（使用4个进程）
pytest -n 4
```

### 4. 环境配置

#### 测试环境变量
```bash
# 设置测试环境
export TESTING=true
export LOG_LEVEL=DEBUG

# 或者使用 .env.test 文件
cp .env.template .env.test
# 编辑测试相关配置
```

#### 数据库配置
```bash
# 使用测试数据库
export DB_PATH=test.db
export TEST_MODE=true
```

## 测试最佳实践 (Testing Best Practices)

### 1. 测试命名约定
```python
# ✅ 好的测试命名
def test_leader_should_decompose_complex_task_into_subtasks():
    """测试 Leader 应该将复杂任务分解为子任务"""
    pass

def test_dual_reasoner_should_iterate_until_completion():
    """测试双模型推理器应该迭代直到完成"""
    pass

# ❌ 不好的测试命名
def test_leader():
    pass

def test_reasoner_works():
    pass
```

### 2. 测试数据管理
```python
# ✅ 使用 pytest fixture 管理测试数据
@pytest.fixture
def sample_job():
    """标准测试作业"""
    return Job(
        id="test-job-123",
        goal="测试任务目标",
        context="测试上下文信息",
        session_id="test-session"
    )

@pytest.fixture
def complex_job_graph():
    """复杂作业依赖图"""
    # 创建包含多个依赖关系的测试图
    pass
```

### 3. 模拟和存根 (Mocking & Stubbing)
```python
from unittest.mock import Mock, AsyncMock, patch

# ✅ 模拟外部依赖
@patch('app.core.reasoner.model_service.ModelService')
async def test_reasoner_with_mocked_llm(mock_model_service):
    """使用模拟 LLM 服务的推理器测试"""
    mock_model_service.generate.return_value = "模拟 LLM 响应"
    # 测试逻辑...

# ✅ 异步模拟
@pytest.fixture
def mock_async_service():
    service = Mock()
    service.async_method = AsyncMock(return_value="异步结果")
    return service
```

### 4. 断言最佳实践
```python
# ✅ 具体和有意义的断言
def test_job_decomposition():
    subtasks = leader.decompose_task(complex_task)
    
    assert len(subtasks) == 3, "应该分解为3个子任务"
    assert subtasks[0].type == TaskType.ANALYSIS, "第一个任务应该是分析任务"
    assert all(task.dependencies for task in subtasks[1:]), "非首个任务应该有依赖"

# ❌ 模糊的断言
def test_job_decomposition():
    result = leader.decompose_task(task)
    assert result  # 太模糊
    assert len(result) > 0  # 不够具体
```

### 5. 异常测试
```python
# ✅ 测试异常情况
def test_reasoner_should_raise_error_for_invalid_task():
    """测试推理器对无效任务应该抛出异常"""
    with pytest.raises(ValueError, match="任务格式无效"):
        reasoner.infer(invalid_task)

async def test_leader_should_handle_expert_failure_gracefully():
    """测试 Leader 应该优雅地处理专家失败"""
    # 模拟专家执行失败
    with patch.object(expert, 'execute', side_effect=Exception("专家故障")):
        result = await leader.execute_experts([expert])
        assert result.status == ExecutionStatus.PARTIAL_SUCCESS
```

## 测试覆盖率分析 (Test Coverage Analysis)

### 当前覆盖率概况
基于现有测试文件分析，主要覆盖区域：

#### 高覆盖率模块 (>80%)
- **推理器模块**: `test_dual_model_reasoner.py`, `test_mono_model_reasoner.py`
- **工作流模块**: `test_workflow.py`, `test_operator.py`
- **SDK 包装器**: `wrapper/` 目录下的测试

#### 中等覆盖率模块 (50-80%)
- **智能体模块**: `test_leader_execution.py`
- **记忆系统**: `test_memory_service.py`, `test_memory_hooks.py`
- **工具包**: `test_toolkit.py`

#### 待提升覆盖率模块 (<50%)
- **服务层**: 数据库访问、持久化服务
- **插件系统**: 各种插件的集成测试
- **错误处理**: 异常流程的测试覆盖

### 覆盖率提升建议
```python
# 需要添加的测试用例

class TestDatabaseIntegration:
    """数据库集成测试"""
    
    def test_job_persistence(self):
        """测试作业持久化"""
        pass
        
    def test_message_storage_and_retrieval(self):
        """测试消息存储和检索"""
        pass

class TestPluginSystem:
    """插件系统测试"""
    
    def test_knowledge_store_plugin_loading(self):
        """测试知识存储插件加载"""
        pass
        
    def test_model_service_plugin_switching(self):
        """测试模型服务插件切换"""
        pass

class TestErrorScenarios:
    """错误场景测试"""
    
    def test_network_failure_handling(self):
        """测试网络故障处理"""
        pass
        
    def test_resource_exhaustion_recovery(self):
        """测试资源耗尽恢复"""
        pass
```

## 性能和基准测试 (Performance & Benchmark Testing)

### GAIA 基准测试详解

#### 测试配置 - `gaia_agents.yml`
```yaml
agents:
  - name: "数据分析专家"
    type: "domain_expert"
    capabilities:
      - "数据处理"
      - "统计分析"
      - "可视化"
  
  - name: "推理专家"
    type: "reasoning_expert" 
    capabilities:
      - "逻辑推理"
      - "问题分解"
      - "结果聚合"
```

#### 运行基准测试
```python
# test/benchmark/gaia/run_hf_gaia_test.py
def run_gaia_benchmark():
    """运行 GAIA 基准测试"""
    
    # 1. 加载数据集
    dataset = load_gaia_dataset()
    
    # 2. 初始化智能体
    agents = load_agents_from_config("gaia_agents.yml")
    
    # 3. 运行测试用例
    results = []
    for test_case in dataset:
        result = evaluate_agent_performance(agents, test_case)
        results.append(result)
    
    # 4. 生成报告
    generate_benchmark_report(results)
```

### 性能指标监控
```python
class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {
            "response_time": [],
            "memory_usage": [],
            "token_consumption": [],
            "success_rate": 0.0
        }
    
    def record_execution(self, start_time, end_time, memory_delta, tokens_used):
        """记录执行性能数据"""
        response_time = end_time - start_time
        self.metrics["response_time"].append(response_time)
        self.metrics["memory_usage"].append(memory_delta)
        self.metrics["token_consumption"].append(tokens_used)
    
    def generate_report(self):
        """生成性能报告"""
        return {
            "avg_response_time": sum(self.metrics["response_time"]) / len(self.metrics["response_time"]),
            "max_memory_usage": max(self.metrics["memory_usage"]),
            "total_tokens": sum(self.metrics["token_consumption"]),
            "success_rate": self.metrics["success_rate"]
        }
```

---

## 测试环境管理 (Test Environment Management)

### 1. 测试环境隔离
```bash
# 创建独立的测试环境
poetry install --with test

# 设置测试专用配置
export ENVIRONMENT=test
export DB_PATH=":memory:"  # 使用内存数据库
export MOCK_EXTERNAL_SERVICES=true
```

### 2. 测试数据清理
```python
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """自动清理测试数据"""
    yield  # 运行测试
    
    # 清理操作
    cleanup_test_database()
    clear_test_cache()
    reset_global_state()
```

### 3. CI/CD 集成
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --with test
    
    - name: Run tests
      run: |
        poetry run pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

通过完善的测试体系，Chat2Graph 确保了高质量的代码交付和稳定的系统运行，为生产环境部署提供了可靠的质量保证。

---

## 相关文档链接

- [架构总览](../Architecture/Overview.md) - 了解被测试的系统架构
- [代码精粹分析](../Code-Analysis/Highlights.md) - 学习优秀的代码实践
- [潜在问题与改进建议](../Code-Analysis/Issues-and-Suggestions.md) - 查看需要重点测试的问题区域