import asyncio

from app.core.agent.expert import Expert
from app.core.model.message import TextMessage
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.sdk.agentic_service import AgenticService
from app.core.sdk.legacy.graph_modeling import (
    CONCEPT_MODELING_INSTRUCTION,
    CONCEPT_MODELING_OUTPUT_SCHEMA,
    CONCEPT_MODELING_PROFILE,
    DOC_ANALYSIS_INSTRUCTION,
    DOC_ANALYSIS_OUTPUT_SCHEMA,
    DOC_ANALYSIS_PROFILE,
    concept_identification_action,
    consistency_check_action,
    content_understanding_action,
    entity_type_definition_action,
    graph_validation_action,
    relation_pattern_recognition_action,
    relation_type_definition_action,
    schema_design_action,
    self_reflection_schema_action,
)
from app.core.sdk.wrapper.agent_wrapper import AgentWrapper
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper
from app.core.toolkit.toolkit import ToolkitService


async def main():
    """Main function."""
    agentic_service = AgenticService("Chat2Graph").load()

    # set the user message
    user_message = TextMessage(payload="通过工具来阅读原文，我需要对《三国演义》中的关系进行建模。")

    # toolkit service
    analysis_toolkit = ToolkitWrapper().chain(
        (
            content_understanding_action,
            concept_identification_action,
            relation_pattern_recognition_action,
            consistency_check_action,
        ),
    )
    analysis_toolkit_service = ToolkitService(toolkit=analysis_toolkit)
    concept_modeling_toolkit = ToolkitWrapper().chain(
        (
            entity_type_definition_action,
            relation_type_definition_action,
            self_reflection_schema_action,
            schema_design_action,
            graph_validation_action,
        ),
    )
    concept_modeling_toolkit_service = ToolkitService(toolkit=concept_modeling_toolkit)

    # operator
    analysis_operator = (
        OperatorWrapper()
        .instruction(DOC_ANALYSIS_PROFILE + DOC_ANALYSIS_INSTRUCTION)
        .output_schema(DOC_ANALYSIS_OUTPUT_SCHEMA)
        .actions(
            [
                content_understanding_action,
                concept_identification_action,
                relation_pattern_recognition_action,
                consistency_check_action,
            ]
        )
        .service(analysis_toolkit_service)
        .build()
    )
    concept_modeling_operator = (
        OperatorWrapper()
        .instruction(CONCEPT_MODELING_PROFILE + CONCEPT_MODELING_INSTRUCTION)
        .output_schema(CONCEPT_MODELING_OUTPUT_SCHEMA)
        .actions(
            [
                entity_type_definition_action,
                relation_type_definition_action,
                self_reflection_schema_action,
                schema_design_action,
                graph_validation_action,
            ]
        )
        .service(concept_modeling_toolkit_service)
        .build()
    )

    # workflow
    workflow = WorkflowWrapper().chain((analysis_operator, concept_modeling_operator))

    # expert
    expert = (
        AgentWrapper()
        .type(Expert)
        .name("Graph Modeling Expert")
        .description(CONCEPT_MODELING_PROFILE + CONCEPT_MODELING_INSTRUCTION)
        .reasoner(DualModelReasoner())
        .workflow(workflow)
        .build()
    )
    agentic_service.expert(expert)

    # submit the job
    session = agentic_service.session()
    job = await session.submit(user_message)
    service_message = await session.wait(job.id)

    # print the result
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    asyncio.run(main())
