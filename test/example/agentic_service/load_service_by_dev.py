import asyncio

from app.agent.agent import AgentConfig, Profile
from app.agent.graph_agent.graph_modeling import (
    CONCEPT_MODELING_PROFILE,
    DOC_ANALYSIS_INSTRUCTION,
    DOC_ANALYSIS_OUTPUT_SCHEMA,
    DOC_ANALYSIS_PROFILE,
    content_understanding_action,
)
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.agentic_service import AgenticService
from app.memory.message import TextMessage
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.toolkit.toolkit import ToolkitService


async def main():
    """Main function."""
    agentic_service = AgenticService("Chat2Graph").load()

    # set the user message
    user_message = TextMessage(
        payload=(
            "首先我需要对《三国演义》中的关系进行建模，然后我会给你《三国演义》的部分文档，你需要把数据导入到图数据库中（建立一个全面的知识图谱）。最后基于构建好的图数据库，我希望了解曹操的故事以及影响力。"
            "《三国演义》中的曹操是一个充满争议的历史人物。他既是一个雄才大略的枭雄，也是一个爱才惜才的领袖；既是一个残暴的统治者，也是一个浪漫的诗人。通过图谱分析，我们将从数据的角度来解读这位复杂的历史人物。"
        ),
    )

    # toolkit service
    tookit_service = ToolkitService().chain(content_understanding_action)

    # operator
    operator_config = OperatorConfig(
        instruction=DOC_ANALYSIS_PROFILE + DOC_ANALYSIS_INSTRUCTION,
        output_schema=DOC_ANALYSIS_OUTPUT_SCHEMA,
        actions=[content_understanding_action],
    )
    operator = Operator(config=operator_config, toolkit_service=tookit_service)

    # workflow
    workflow = DbgptWorkflow().chain(operator)

    # expert
    expert_config = AgentConfig(
        profile=Profile(name="Graph Modeling Expert", description=CONCEPT_MODELING_PROFILE),
        reasoner=DualModelReasoner(),
        workflow=workflow,
    )
    agentic_service.expert(expert_config)

    # submit the job
    session = agentic_service.session()
    job = await session.submit(user_message)
    service_message = await session.wait(job.id)

    # print the result
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    asyncio.run(main())
