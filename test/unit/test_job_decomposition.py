from typing import Any, List, Optional
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.agent.agent import AgentConfig, Profile
from app.core.agent.builtin_leader_state import BuiltinLeaderState
from app.core.agent.leader import Leader
from app.core.common.singleton import AbcSingleton
from app.core.model.job import Job, SubJob
from app.core.model.job_graph import JobGraph
from app.core.model.message import AgentMessage, WorkflowMessage
from app.core.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.reasoner.reasoner import Reasoner
from app.core.sdk.agentic_service import AgenticService
from app.core.service.job_service import JobService
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.workflow.workflow import Workflow
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow

AgenticService()


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

    def _execute_workflow(
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
        id="job_decomp_operator_id" + str(uuid4()),
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

    # create the main job and the existing subjob
    job = Job(goal="The tested main job")
    job_service: JobService = JobService.instance
    job_service.save_job(job)
    sub_job = SubJob(
        goal="extract entities from text",
        original_job_id=job.id,
        expert_id=leader.state.get_expert_by_name("Expert 1").get_id(),
    )
    job_service.save_job(sub_job)

    # configure the initial job graph
    job_service.add_job(
        original_job_id=job.id,
        job=sub_job,
        expert_id=leader.state.get_expert_by_name("Expert 1").get_id(),
        predecessors=[],
        successors=[],
    )
    initial_job_graph: JobGraph = job_service.get_job_graph(job.id)

    job_graph = leader.execute(AgentMessage(job_id=job.id))
    job_service.replace_subgraph(job.id, new_subgraph=job_graph, old_subgraph=initial_job_graph)

    assert isinstance(job_graph, JobGraph)

    assert len(job_service.get_job_graph(job.id).vertices()) == 3
    assert len(job_service.get_job_graph(job.id).edges()) == 3  # 3 dependencies

    assert job_service.get_subjob(sub_job.id).is_legacy


@pytest.mark.asyncio
async def test_execute_error_handling(leader: Leader, mock_reasoner: AsyncMock):
    """Test job decomposition with empty job."""
    mock_response = """<Initial state ψ>
Analyzing the task...

∴ Ops! No subtasks found.
"""
    mock_reasoner.infer.return_value = mock_response

    job_service: JobService = JobService.instance

    original_job = Job(goal="")
    job_service.save_job(original_job)
    subjob = SubJob(goal="", original_job_id=original_job.id, expert_id=leader._id)
    job_service.save_job(subjob)

    job_service.add_job(
        original_job_id=original_job.id,
        job=subjob,
        expert_id=leader._id,  # it is not a good idea to use the private attribute,
        # but it is ok for now
        predecessors=[],
        successors=[],
    )

    with pytest.raises(Exception) as exc_info:
        job_graph = leader.execute(AgentMessage(job_id=subjob.id))
        job_service.replace_subgraph(new_subgraph=job_graph)

    assert "Failed to decompose the subjobs by json format" in str(exc_info.value)
    assert mock_response in str(exc_info.value)
