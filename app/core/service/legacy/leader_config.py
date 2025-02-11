from typing import Optional

from app.core.agent.agent import AgentConfig, Profile
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.core.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA, JOB_DECOMPOSITION_PROMPT
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
