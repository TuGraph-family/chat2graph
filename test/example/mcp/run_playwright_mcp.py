import asyncio

from app.core.common.type import McpTransportType, ToolGroupType
from app.core.model.job import SubJob
from app.core.service.reasoner_service import ReasonerService
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.mcp_service import McpService
from app.core.toolkit.tool_config import McpConfig, McpTransportConfig
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from test.resource.init_server import init_server

init_server()


async def main():
    """Main function to demonstrate an agentic Operator for information seeking."""
    # register Actions and Tools to ToolkitService
    browse_action = Action(
        id="browse_webpage",
        name="Browse Webpage",
        description="Uses a web browsing tool to visit a given URL and retrieve its raw HTML content for analysis.",
    )
    analyze_action = Action(
        id="analyze_content",
        name="Analyze Content",
        description="Intelligently analyzes provided text or HTML content to find, extract, and understand specific information relevant to the user's goal.",
    )
    generate_action = Action(
        id="generate_response",
        name="Generate Final Response",
        description="Synthesizes all gathered and analyzed information to formulate a final, comprehensive answer for the user.",
    )
    # make sure the MCP server is started and running on the specified port
    # e.g. npx @playwright/mcp@latest --port 8931
    browsing_tool = McpService(
        mcp_config=McpConfig(
            type=ToolGroupType.MCP,
            name="Playwright Browsing Tool Group",
            transport_config=McpTransportConfig(
                transport_type=McpTransportType.SSE,
                url="http://localhost:8931/sse",
            ),
        )
    )

    toolkit_service: ToolkitService = ToolkitService.instance
    toolkit_service.add_action(
        action=browse_action, next_actions=[(analyze_action, 0.9)], prev_actions=[]
    )
    toolkit_service.add_action(
        action=analyze_action,
        prev_actions=[(browse_action, 0.9)],
        next_actions=[(generate_action, 0.8)],
    )
    toolkit_service.add_action(
        action=generate_action, next_actions=[], prev_actions=[(analyze_action, 0.8)]
    )

    toolkit_service.add_tool_group(
        tool_group=browsing_tool,
        connected_actions=[(browse_action, 1.0)],
    )

    # config Reasoner
    reasoner_service: ReasonerService = ReasonerService.instance
    reasoner = reasoner_service.get_reasoner()

    # config Operator
    instruction = """You are an autonomous research assistant AI. Your primary function is to use a set of tools to find, process, and synthesize information from the web to answer a user's goal.

Your Thought Process:
1. **REASON**: First, carefully analyze the user's `goal` and the current `context`.
2. **PLAN**: Formulate a high-level plan. Decide which `action` is the most logical next step. For example, if you have no information, your first step is likely 'Browse Webpage'. If you have raw content, the next step is to 'Analyze Content'.
3. **EXECUTE**: When you choose an action, the system will execute the corresponding tool for you. For instance, selecting 'Browse Webpage' will trigger the browser tool.
4. **ANALYZE & REFLECT**: After the tool runs, you will receive its output as new context. You must analyze this output. Did you find the information? Do you need to browse a different page? Do you have enough information to form a final answer?
5. **REPEAT or RESPOND**: If more information is needed, repeat the cycle. If you have a definitive answer, choose the 'Generate Final Response' action to deliver it.

Your goal is to be efficient and accurate. Directly address the user's request in your final response.
"""  # noqa: E501
    operator_config = OperatorConfig(
        instruction=instruction,
        actions=[browse_action, analyze_action, generate_action],
        threshold=0.7,
        hops=1,
    )
    operator = Operator(config=operator_config)

    job_goal = "Visit the official OpenAI website, find the company's mission statement, and report it back verbatim."
    job_context = """The user is asking for specific, factual information from a company's homepage. The primary URL to start with is https://openai.com. The agent must first browse this page, then intelligently search the retrieved content for phrases like 'mission', 'our mission', 'our goal', 'about us' etc., to locate the required information."""
    job = SubJob(
        id="job_find_openai_mission",
        session_id="session_agentic_test",
        goal=job_goal,
        context=job_context,
        original_job_id="test_original_job_id",
    )
    result = await operator.execute(reasoner=reasoner, job=job)

    print("-" * 20)
    print("✅ Operator execution completed!")
    print(f"📦 Final Result:\n{result.scratchpad}\n")


if __name__ == "__main__":
    asyncio.run(main())
