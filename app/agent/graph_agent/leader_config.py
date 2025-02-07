from typing import Optional

from app.agent.agent import AgentConfig, Profile
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.common.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA, JOB_DECOMPOSITION_PROMPT
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow


def get_leader_config(reasoner: Optional[Reasoner] = None) -> AgentConfig:
    """Get the leader configuration."""
    # configure the leader
    reasoner = reasoner or DualModelReasoner()
    decomp_operator_config = OperatorConfig(
        id="job_decomp_operator_id",
        instruction=JOB_DECOMPOSITION_PROMPT,
        actions=[],
        output_schema=JOB_DECOMPOSITION_OUTPUT_SCHEMA,
    )
    decomposition_operator = Operator(config=decomp_operator_config)
    leader_workflow = DbgptWorkflow()
    leader_workflow.add_operator(decomposition_operator)
    agent_config = AgentConfig(
        profile=Profile(name="leader"), reasoner=reasoner, workflow=leader_workflow
    )

    return agent_config
