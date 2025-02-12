from typing import Any, List, Optional
from unittest.mock import AsyncMock

import pytest

from app.core.agent.agent import AgentConfig, Profile
from app.core.agent.builtin_leader_state import BuiltinLeaderState
from app.core.agent.leader import Leader
from app.core.common.singleton import AbcSingleton
from app.core.model.job import Job
from app.core.model.job_graph import JobGraph
from app.core.model.message import AgentMessage, WorkflowMessage
from app.core.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.reasoner.reasoner import Reasoner
from app.core.service.job_service import JobService
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.workflow.workflow import Workflow
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow


class MockWorkflow(Workflow):
    """Mock workflow class."""

    def build_workflow(self, reasoner: Reasoner) -> None:
        """Build in the workflow."""

    async def execute(
        self,
        job: Job,
        reasoner: Reasoner,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
    ) -> WorkflowMessage:
        """Execute the workflow."""

    def add_operator(
        self,
        operator: Operator,
        previous_ops: Optional[List[Operator]] = None,
        next_ops: Optional[List[Operator]] = None,
    ) -> None:
        """Add an operator to the workflow."""

    def remove_operator(self, operator: Operator) -> None:
        """Remove an operator from the workflow."""

    def get_operator(self, operator_id: str) -> Optional[Operator]:
        """Get an operator from the workflow."""

    def get_operators(self) -> List[Operator]:
        """Get all operators from the workflow."""

    def visualize(self) -> None:
        """Visualize the workflow."""

    def _build_workflow(self, reasoner: Reasoner) -> Any:
        """Build the workflow."""

    async def _execute_workflow(
        self,
        workflow: Any,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
    ) -> WorkflowMessage:
        """Execute the workflow."""


class MockMessage:
    """Mock message class."""

    def __init__(self, content: str):
        self.content = content


@pytest.fixture
def mock_reasoner():
    """Create a mock reasoner with predefined responses."""
    reasoner = AsyncMock(spec=MonoModelReasoner)
    reasoner.infer = AsyncMock()
    return reasoner


@pytest.fixture
def leader(mock_reasoner: Reasoner):
    """Create a leader instance with mock reasoner."""
    # clear the AbcSingleton instance
    if BuiltinLeaderState in AbcSingleton._instances:
        del AbcSingleton._instances[BuiltinLeaderState]

    if Leader in AbcSingleton._instances:
        del AbcSingleton._instances[Leader]

    decomp_operator_config = OperatorConfig(
        id="job_decomp_operator_id",
        instruction="",
        actions=[],
        output_schema=JOB_DECOMPOSITION_OUTPUT_SCHEMA,
    )
    decomposition_operator = Operator(config=decomp_operator_config)

    workflow = DbgptWorkflow()
    workflow.add_operator(decomposition_operator)

    config = AgentConfig(
        profile=Profile(name="test_name"), reasoner=mock_reasoner, workflow=workflow
    )
    return Leader(agent_config=config)


@pytest.mark.asyncio
async def test_decompose_job_basic(leader: Leader, mock_reasoner: Reasoner):
    """Test basic job decomposition functionality."""
    mock_response = """Initial state <ψ>
Decomposing the task...

∴ So, the following jobs are proposed:

Final Delivery:
为了完成这一目标，我将为我们确定三个具体的子任务：

    ```json
    {
        "subtask_1": 
        {
            "goal": "信息收集, 获取原始文本数据。",
            "context": "需要从各个数据源收集相关文本。",
            "completion_criteria": "成功收集到至少100个有效文本样本。",
            "dependencies": [],
            "assigned_expert": "Expert 1"
        },
        "subtask_2":
        {
            "goal": "实体分类, 从文本中识别关键实体。",
            "context": "使用自然语言处理工具进行实体识别。",
            "completion_criteria": "成功识别出至少300个关键实体。",
            "dependencies": ["subtask_1"],
            "assigned_expert": "Expert 2"
        },
        "subtask_3":
        {
            "goal": "结果分析, 验证提取实体与数据模型的一致性。",
            "context": "对已提取的实体进行审查，确保符合图数据库设计要求。",
            "completion_criteria": "审核报告显示95%一致性。",
            "dependencies": ["subtask_1", "subtask_2"],
            "assigned_expert": "Expert 3"
        }
    }
    ```
"""
    mock_reasoner.infer.return_value = mock_response

    job = Job(session_id="test_session_id", goal="extract entities from text")

    expert_profile_1 = AgentConfig(
        profile=Profile(
            name="Expert 1",
            description="Data collection expert",
        ),
        reasoner=mock_reasoner,
        workflow=MockWorkflow(),
    )
    expert_profile_2 = AgentConfig(
        profile=Profile(
            name="Expert 2",
            description="Entity classification expert",
        ),
        reasoner=mock_reasoner,
        workflow=MockWorkflow(),
    )
    expert_profile_3 = AgentConfig(
        profile=Profile(
            name="Expert 3",
            description="Result analysis expert",
        ),
        reasoner=mock_reasoner,
        workflow=MockWorkflow(),
    )
    leader.state.create_expert(expert_profile_1)
    leader.state.create_expert(expert_profile_2)
    leader.state.create_expert(expert_profile_3)

    # configure the initial job graph
    initial_job_graph: JobGraph = JobGraph()
    initial_job_graph.add_node(id=job.id, job=job)
    job_service: JobService = JobService()
    job_service.set_job_graph(job_id=job.id, job_graph=initial_job_graph)

    job_graph = await leader.execute(AgentMessage(job=job))
    print(f"job_graph: {job_graph.nodes}")
    job_service.replace_subgraph(job.id, new_subgraph=job_graph, old_subgraph=initial_job_graph)

    assert isinstance(job_graph, JobGraph)
    assert all(isinstance(node_data["job"], Job) for _, node_data in job_graph.nodes_data())

    assert len(job_service.get_job_graph(job.id).nodes()) == 3
    assert len(job_service.get_job_graph(job.id).edges()) == 3  # 3 dependencies

    assert len(job_service.get_job_graph(job.id)._legacy_jobs.keys()) == 1


@pytest.mark.asyncio
async def test_execute_error_handling(leader: Leader, mock_reasoner: AsyncMock):
    """Test job decomposition with empty job."""
    mock_response = """<Initial state ψ>
Analyzing the task...

∴ Ops! No subtasks found.
"""
    mock_reasoner.infer.return_value = mock_response

    job = Job(session_id="test_session_id", goal="")

    with pytest.raises(Exception) as exc_info:
        job_graph = await leader.execute(AgentMessage(job=job))
        job_service: JobService = JobService.instance
        job_service.replace_subgraph(new_subgraph=job_graph)

    assert "Failed to decompose the subjobs by json format" in str(exc_info.value)
    assert mock_response in str(exc_info.value)
