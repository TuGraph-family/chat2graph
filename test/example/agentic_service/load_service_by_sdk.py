import asyncio

from app.core.common.type import PlatformType
from app.core.model.message import TextMessage
from app.core.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA, JOB_DECOMPOSITION_PROMPT
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
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper


async def main():
    """Main function."""
    mas = AgenticService("Chat2Graph")

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
        .build()
        .toolkit_chain(
            (
                content_understanding_action,
                concept_identification_action,
                relation_pattern_recognition_action,
                consistency_check_action,
            ),
        )
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
        .build()
        .toolkit_chain(
            (
                entity_type_definition_action,
                relation_type_definition_action,
                self_reflection_schema_action,
                schema_design_action,
                graph_validation_action,
            ),
        )
    )
    job_decomposition_operator = (
        OperatorWrapper()
        .instruction(JOB_DECOMPOSITION_PROMPT)
        .output_schema(JOB_DECOMPOSITION_OUTPUT_SCHEMA)
        .build()
    )

    # leader & expert
    mas.leader(name="Leader").reasoner(thinker_name="Leader", actor_name="Leader").workflow(
        job_decomposition_operator, platfor_type=PlatformType.DBGPT
    ).build()

    mas.expert(name="Graph Modeling Expert").reasoner(
        thinker_name="Graph Modeling Expert", actor_name="Graph Modeling Expert"
    ).workflow(
        (analysis_operator, concept_modeling_operator), platfor_type=PlatformType.DBGPT
    ).build()

    # set the user message
    user_message = TextMessage(payload="通过工具来阅读原文，我需要对《三国演义》中的关系进行建模。")

    # submit the job
    session = mas.session()
    job_wrapper = await session.submit(user_message)
    service_message = await session.wait(job_wrapper)

    # print the result
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    asyncio.run(main())
