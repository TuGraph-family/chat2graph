from app.core.agent.agent import AgentConfig, Profile
from app.core.agent.leader import Leader
from app.core.model.job import SubJob
from app.core.model.job_graph import JobGraph
from app.core.prompt.operator import EVAL_OPERATION_INSTRUCTION_PROMPT, EVAL_OPERATION_OUTPUT_PROMPT
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.service.job_service import JobService
from app.core.service.service_factory import ServiceFactory
from app.core.workflow.eval_operator import EvalOperator
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow

ServiceFactory.initialize()


def main():
    """Main function for testing leader execute with academic paper analysis."""
    # initialize components
    reasoner = DualModelReasoner()
    agent_config = AgentConfig(
        profile="academic_reviewer", reasoner=reasoner, workflow=DbgptWorkflow()
    )
    leader = Leader(agent_config=agent_config)

    # paper content (simplified for demonstration)
    paper_content = """
paper content:
    Mixture-of-Experts (MoE) architectures have emerged as a promising solution for managing computational costs when scaling up parameters in large language models (LLMs). Recent applications
    of MoE in Transformer-based models (Vaswani et al., 2017) have led to successful attempts at scaling language models to substantial sizes (Shao et al., 2024; DeepSeek-AI et al., 2024; Dai et al.,
    2024; Fedus et al., 2021; Lepikhin et al., 2020), resulting in remarkable performance improvements.
    However, training MoE models always face the circumstance of load imbalance, which may result
    in routing collapse (Shazeer et al., 2017) or increased computational overhead (Fedus et al., 2021;
    Lepikhin et al., 2020; Shazeer et al., 2017). In order to avoid imbalanced routing, existing methods (Fedus et al., 2021; Lepikhin et al., 2020) commonly use an auxiliary loss to encourage balanced
    expert load. Although the auxiliary loss can alleviate load imbalance during training, it also introduces undesired gradients that conflict with the language modeling objective. These interference
    gradients will impair the model performance, so existing MoE methods always need to consider the
    trade-off between load balance and model performance.

    In this paper, we propose Loss-Free Balancing, an auxiliary-loss-free load balancing strategy,
    aiming at maintaining control over expert load balance while not introducing interference gradients.
    Loss-Free Balancing features an iterative process of token routing and bias updating. As illustrated
    in Figure 1, before the top-K routing decision of MoE, Loss-Free Balancing will first apply expertwise biases to the original routing scores to produce biased gating scores, which determine the actual
    routing targets of each token during training. These expert-wise biases will keep updating according
    to the expert load observed on recent training tokens, where the biases of heavy-load experts will be
    depressed and those of lite-load experts will be elevated. Through this dynamic updating strategy,
    Loss-Free Balancing ensures that the biased gating scores can consistently lead to balanced routing
    results. Compared with the auxiliary-loss-controlled load balancing strategies, Loss-Free Balancing
    does not introduce undesired gradients that disrupt the primary language modeling objective, so its
    training process is more noise-free and friendly.

    In order to validate the performance of Loss-Free Balancing, we train MoE language models
    with 1B parameters on 100B tokens and 3B parameters on 200B tokens from scratch. Experimental
    results demonstrate that Loss-Free Balancing produces MoE models with better validation loss than
    traditional auxiliary-loss-controlled models. Meanwhile, keeping the performance advantage, LossFree Balancing also achieves a significantly better load balance at the global and batch levels, and
    is naturally compatible with expert parallelism, which is usually employed for training extremely
    large MoE models.

    ...
    """  # noqa: E501

    # create jobs for paper analysis
    job_1 = SubJob(
        id="extract_key_info",
        session_id="paper_analysis_session",
        goal="Identify and extract the core information from the paper, including research problem, proposed solution, and key findings. Ensure to preserve key supporting details and specific examples related to these core elements.",  # noqa: E501
        context=paper_content,
        output_schema="string",
    )

    job_2 = SubJob(
        id="analyze_methodology",
        session_id="paper_analysis_session",
        goal="Analyze the paper's methodology to understand its research approach, considering aspects like research design, data sources, and analytical techniques.",  # noqa: E501
        context=paper_content,
        output_schema="string",
    )

    job_3 = SubJob(
        id="analyze_results",
        session_id="paper_analysis_session",
        goal="Analyze the paper's results and discuss their implications, focusing on key findings, statistical evidence, and practical significance.",  # noqa: E501
        context=paper_content,
        output_schema="string",
    )

    job_4 = SubJob(
        id="technical_review",
        session_id="paper_analysis_session",
        goal="Evaluate the technical soundness of the paper's methodology and analysis, assessing methodological rigor, validity of analysis, and potential limitations.",  # noqa: E501
        context=paper_content,
        output_schema="string",
    )

    job_5 = SubJob(
        id="generate_summary",
        session_id="paper_analysis_session",
        goal="Synthesize a detailed comprehensive summary based on the methodology and results analyses, highlighting the paper's main contributions and significance. Incorporate key supporting details and specific findings from the analyses to provide a rich and informative summary.",  # noqa: E501
        context=paper_content,
        output_schema="string",
    )

    # create workflows and expert profiles
    expert_configs = [
        (
            "Information Extractor",
            "Extracts and organizes key information from academic papers to create a structured foundation for analysis.",  # noqa: E501
            "You are a highly efficient research assistant specializing in extracting and organizing key information from academic papers. Your primary focus is to build a structured foundation for subsequent analysis by other experts. Please focus on:\n"  # noqa: E501
            "1. **Clearly identify the core research problem or question** the paper addresses.\n"
            "2. **Summarize the proposed solution or approach** to address the research problem.\n"
            "3. **Extract the key findings and main conclusions** presented in the paper.\n"
            "4. **Organize your response in a structured format using Markdown**, with clear sections for 'Research Problem', 'Proposed Solution', and 'Key Findings'. Use bullet points or numbered lists within each section to enhance readability and organization. This structured output will be used by other experts for in-depth analysis.",  # noqa: E501
        ),
        (
            "Methodology Expert",
            "Provides in-depth evaluation of research methodology and study design, offering actionable recommendations.",  # noqa: E501
            "You are a seasoned methodology expert with a specialization in research design analysis. Your task is to conduct an in-depth evaluation of the paper's methodology and study design, and provide actionable recommendations for improvement or further consideration. Please evaluate:\n"  # noqa: E501
            "1. **The appropriateness and rigor of the research design** chosen for the study's objectives.\n"  # noqa: E501
            "2. **The adequacy of the sampling methods and sample size** in representing the target population and ensuring generalizability.\n"  # noqa: E501
            "3. **The clarity and validity of the data collection procedures**, including instruments and protocols.\n"  # noqa: E501
            "4. **Potential methodological limitations and biases** that might affect the study's findings and conclusions.\n"  # noqa: E501
            "Provide a detailed analysis for each point, justifying your evaluation with references to established methodological principles where possible. Conclude with a summary of your overall assessment and specific, actionable recommendations for strengthening the methodology in future research or similar studies.",  # noqa: E501
        ),
        (
            "Results Analyst",
            "Analyzes research results, interprets findings in context, and discusses practical and theoretical implications.",  # noqa: E501
            "You are a highly skilled results analyst specializing in the interpretation of research findings and their implications. Your role is to rigorously analyze the research results presented in the paper, interpret them within the broader context of the field, and discuss their practical and theoretical significance. Please analyze:\n"  # noqa: E501
            "1. **The strength of evidence supporting the key findings**, moving beyond just statistical significance to consider effect sizes and robustness.\n"  # noqa: E501
            "2. **The interpretation of the results in the specific context of the research**, considering alternative explanations and potential confounding factors.\n"  # noqa: E501
            "3. **The practical implications of the findings**, including their potential impact on real-world applications or interventions.\n"  # noqa: E501
            "4. **The theoretical contributions of the research**, and how the findings contribute to or challenge existing theories and frameworks.\n"  # noqa: E501
            "Present your analysis with clear reasoning and evidence from the paper, ensuring that your interpretations are well-supported and insightful.  Conclude with a concise summary of the key implications and contributions of the research results.",  # noqa: E501
        ),
        (
            "Technical Reviewer",
            "Conducts a thorough technical review of the research, focusing on statistical and analytical soundness and offering constructive feedback.",  # noqa: E501
            "You are a meticulous technical reviewer specializing in the statistical and analytical soundness of research. Your responsibility is to conduct a thorough technical review of the paper, focusing on the rigor and validity of the methods and analyses employed. Please review:\n"  # noqa: E501
            "1. **The appropriateness of the statistical and analytical methods** used, given the research questions and data types.\n"  # noqa: E501
            "2. **The accuracy and correctness of the data analysis procedures** and computations.\n"  # noqa: E501
            "3. **The overall technical accuracy and rigor** of the research methodology and analysis.\n"  # noqa: E501
            "4. **Potential concerns regarding the validity and reliability** of the findings from a technical perspective.\n"  # noqa: E501
            "Provide a technical evaluation that is both critical and constructive. For each point, identify both strengths and areas of concern, offering specific feedback to enhance the technical quality of the research. Your review should be detailed and technically precise, aimed at ensuring the highest standards of research integrity.",  # noqa: E501
        ),
        (
            "Research Synthesizer",
            "Synthesizes analyses from methodology and results experts into a coherent narrative, providing holistic evaluation and future directions.",  # noqa: E501
            "You are an expert research synthesizer with a talent for integrating diverse analyses into a cohesive and insightful summary. Your task is to create a comprehensive and coherent narrative that synthesizes the analyses provided by the Methodology Expert and the Results Analyst. Your summary should:\n"  # noqa: E501
            "1. **Synthesize the key evaluations from both the methodology and results analyses**, identifying common themes and points of convergence or divergence.\n"  # noqa: E501
            "2. **Highlight the key strengths and limitations of the research** based on the integrated expert evaluations.\n"  # noqa: E501
            "3. **Provide a holistic and insightful overall evaluation** of the paper's contribution and quality, considering both methodological rigor and the significance of the findings.\n"  # noqa: E501
            "4. **Suggest potential directions for future research** that build upon the current study, addressing its limitations or expanding upon its findings.\n"  # noqa: E501
            "Create a coherent and well-structured narrative that seamlessly integrates all previous analyses, offering a comprehensive and balanced perspective on the paper's merits and areas for future development. Your synthesis should be the definitive summary that provides actionable insights and a clear understanding of the paper's overall value and impact.",  # noqa: E501
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

        leader.state.create_expert(
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

    job_service: JobService = JobService()
    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_1,
        expert_id=leader.state.get_expert_by_name("Information Extractor").get_id(),
        predecessors=[],
        successors=[job_2, job_3],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_2,
        expert_id=leader.state.get_expert_by_name("Methodology Expert").get_id(),
        predecessors=[job_1],
        successors=[job_4],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_3,
        expert_id=leader.state.get_expert_by_name("Results Analyst").get_id(),
        predecessors=[job_1],
        successors=[job_5],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_4,
        expert_id=leader.state.get_expert_by_name("Technical Reviewer").get_id(),
        predecessors=[job_2],
        successors=[job_5],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_5,
        expert_id=leader.state.get_expert_by_name("Research Synthesizer").get_id(),
        predecessors=[job_3, job_4],
        successors=[],
    )

    # execute job graph
    print("\n=== Starting Paper Analysis ===")
    leader.execute_job_graph(job_graph=job_service.get_job_graph("test_original_job_id"))
    job_graph: JobGraph = job_service.get_job_graph("test_original_job_id")
    tail_vertices = [vertex for vertex in job_graph.vertices() if job_graph.out_degree(vertex) == 0]

    for tail_vertex in tail_vertices:
        job = job_graph.get_job(tail_vertex)
        job_result = job_graph.get_job_result(tail_vertex)
        if not job_result:
            print(f"Job {tail_vertex} is not completed yet.")
            continue
        print(f"\nTask {job.id}:")
        print(f"Status: {job_result.status}")
        print(f"Output: {job_result.result.get_payload()}")
        print("-" * 50)


if __name__ == "__main__":
    main()
