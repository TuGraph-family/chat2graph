import asyncio

import networkx as nx  # type: ignore

from app.agent.agent import AgentConfig, Profile
from app.agent.job import SubJob
from app.agent.leader import Leader
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.workflow.operator.eval_operator import EvalOperator
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.common.prompt.operator import (
    EVAL_OPERATION_INSTRUCTION_PROMPT,
    EVAL_OPERATION_OUTPUT_PROMPT,
)
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow


async def main():
    """Main function for testing leader execute with academic paper analysis."""
    # initialize components
    reasoner = DualModelReasoner()
    agent_config = AgentConfig(
        profile="academic_reviewer", reasoner=reasoner, workflow=DbgptWorkflow()
    )
    leader = Leader(agent_config=agent_config)

    # Paper content (simplified for demonstration)
    paper_content = """
    paper content:
        Title: Impact of Social Media on Mental Health During COVID-19 Pandemic
        Abstract: This study investigates the relationship between social media usage and mental health during the COVID-19 pandemic, focusing on anxiety levels, depression symptoms, and overall psychological well-being. Our findings indicate that excessive social media exposure is significantly associated with increased mental health challenges, while moderate and purposeful use may provide social support during isolation periods.
        Methods: We conducted a mixed-methods study involving 1000 participants (ages 18-65) recruited through online platforms. The quantitative component included standardized psychological assessments (GAD-7, PHQ-9) and custom social media usage questionnaires. The qualitative phase comprised semi-structured interviews with 50 selected participants to explore their experiences in depth. Data collection occurred between March 2021 and December 2021, spanning various pandemic phases.
        Results: Our analysis revealed a significant correlation between increased social media use and anxiety levels (r = 0.68, p < 0.001). Participants spending more than 4 hours daily on social media platforms showed higher depression scores (M = 12.4, SD = 3.2) compared to moderate users (M = 8.2, SD = 2.8). Qualitative findings identified three major themes: information overload, social connection maintenance, and emotional contagion. Notably, 73% of participants reported experiencing heightened anxiety after consuming COVID-19 related content on social media.
        Discussion: The findings suggest that while social media served as a crucial communication tool during lockdowns, excessive exposure to pandemic-related content contributed to psychological distress. However, moderate usage focusing on maintaining social connections showed protective effects against isolation-induced mental health challenges. These results highlight the need for balanced social media engagement and digital wellness strategies during crisis periods. Future research should explore interventions to promote healthy social media habits and investigate long-term mental health impacts post-pandemic.
    """  # noqa: E501

    # create jobs for paper analysis
    job_1 = SubJob(
        id="extract_key_info",
        session_id="paper_analysis_session",
        goal="Extract key information from the paper including research goals, methods, and main findings",
        context=paper_content,
        output_schema="string",
    )

    job_2 = SubJob(
        id="analyze_methodology",
        session_id="paper_analysis_session",
        goal="Analyze the research methodology, including study design, data collection, and analytical approaches",
        context="",
        output_schema="string",
    )

    job_3 = SubJob(
        id="analyze_results",
        session_id="paper_analysis_session",
        goal="Analyze the results and their implications, including statistical significance and practical impact",
        context="",
        output_schema="string",
    )

    job_4 = SubJob(
        id="technical_review",
        session_id="paper_analysis_session",
        goal="Review technical soundness of the methodology and statistical analysis",
        context="",
        output_schema="string",
    )

    job_5 = SubJob(
        id="generate_summary",
        session_id="paper_analysis_session",
        goal="Generate a comprehensive summary combining methodology analysis and results analysis",
        context="",
        output_schema="string",
    )

    # create workflows and expert profiles
    expert_configs = [
        (
            "Information Extractor",
            "Extracts and organizes key information from academic papers",
            "You are a research assistant specializing in extracting key information from academic papers. Focus on:\n"
            "1. Research objectives and hypotheses\n"
            "2. Key methodological approaches\n"
            "3. Main findings and conclusions\n"
            "Format your response in a structured way with clear sections.",
        ),
        (
            "Methodology Expert",
            "Specializes in research methodology and study design analysis",
            "You are a methodology expert specializing in research design analysis. Evaluate:\n"
            "1. Research design appropriateness\n"
            "2. Sampling methods and sample size adequacy\n"
            "3. Data collection procedures\n"
            "4. Potential methodological limitations\n"
            "Provide a detailed analysis with specific recommendations if applicable.",
        ),
        (
            "Results Analyst",
            "Focuses on analyzing research results and implications",
            "You are a results analyst specializing in research findings interpretation. Analyze:\n"
            "1. Statistical significance of findings\n"
            "2. Effect sizes and practical significance\n"
            "3. Results interpretation in context\n"
            "4. Implications for theory and practice\n"
            "Present your analysis with clear evidence and reasoning.",
        ),
        (
            "Technical Reviewer",
            "Reviews technical and statistical aspects of research",
            "You are a technical reviewer specializing in statistical analysis. Review:\n"
            "1. Statistical methods appropriateness\n"
            "2. Data analysis procedures\n"
            "3. Technical accuracy and rigor\n"
            "4. Validity and reliability concerns\n"
            "Provide a technical evaluation with specific points of strength and concern.",
        ),
        (
            "Research Synthesizer",
            "Synthesizes multiple analyses into coherent summaries",
            "You are a research synthesizer specializing in integrating diverse analyses. Create a comprehensive summary that:\n"
            "1. Synthesizes methodology and results analyses\n"
            "2. Highlights key strengths and limitations\n"
            "3. Provides overall evaluation\n"
            "4. Suggests future research directions\n"
            "Create a coherent narrative that integrates all previous analyses.",
        ),
    ]

    for name, desc, instruction in expert_configs:
        workflow = DbgptWorkflow()

        op = Operator(
            config=OperatorConfig(
                id=f"{name.lower().replace(' ', '_')}_operator",
                instruction=instruction,
                actions=[],
                output_schema="detalied delivery in string",
            )
        )

        evaluator = EvalOperator(
            config=OperatorConfig(
                instruction=EVAL_OPERATION_INSTRUCTION_PROMPT,
                actions=[],
                output_schema=EVAL_OPERATION_OUTPUT_PROMPT,
            )
        )

        workflow.add_operator(op)
        workflow.set_evaluator(evaluator)

        leader._leader_state.add_expert_config(
            agent_config=AgentConfig(
                profile=Profile(name=name, description=desc),
                reasoner=reasoner,
                workflow=workflow,
            ),
        )

    # Create job graph structure
    #            job_2 (Methodology) → job_4 (Technical)
    #          ↗                                       ↘
    # job_1 (Extract)                                   job_5 (Summary)
    #          ↘                                       ↗
    #            job_3 (Results)

    leader._leader_state.add_job(
        main_job_id="test_main_job_id",
        job=job_1,
        expert_name="Information Extractor",
        predecessors=[],
        successors=[job_2, job_3],
    )

    leader._leader_state.add_job(
        main_job_id="test_main_job_id",
        job=job_2,
        expert_name="Methodology Expert",
        predecessors=[job_1],
        successors=[job_4],
    )

    leader._leader_state.add_job(
        main_job_id="test_main_job_id",
        job=job_3,
        expert_name="Results Analyst",
        predecessors=[job_1],
        successors=[job_5],
    )

    leader._leader_state.add_job(
        main_job_id="test_main_job_id",
        job=job_4,
        expert_name="Technical Reviewer",
        predecessors=[job_2],
        successors=[job_5],
    )

    leader._leader_state.add_job(
        main_job_id="test_main_job_id",
        job=job_5,
        expert_name="Research Synthesizer",
        predecessors=[job_3, job_4],
        successors=[],
    )

    # execute job graph
    print("\n=== Starting Paper Analysis ===")
    job_graph: nx.DiGraph = await leader.execute_job_graph(
        job_graph=leader._leader_state.get_job_graph(main_job_id="test_main_job_id")
    )
    tail_nodes = [node for node in job_graph.nodes if job_graph.out_degree(node) == 0]

    for tail_node in tail_nodes:
        job = job_graph.nodes[tail_node]["job"]
        workflow_message = job_graph.nodes[tail_node]["workflow_result"]
        print(f"\nTask {job.id}:")
        print(f"Status: {workflow_message.status}")
        print(f"Output: {workflow_message.scratchpad}")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
