import asyncio
from pathlib import Path
import shutil
import tempfile

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
    """Main function to demonstrate an agentic Operator for file system operations."""
    # Create a temporary directory for the example
    temp_dir = tempfile.mkdtemp(prefix="fs_mcp_example_")
    # Resolve symlinks to get the real path, which is important on macOS
    temp_dir = str(Path(temp_dir).resolve())
    print(f"Created temporary directory: {temp_dir}")

    # Create a sample file in the temporary directory
    sample_file_path = Path(temp_dir) / "sample.txt"
    sample_file_content = "This is a sample file for the MCP file system example."
    with open(sample_file_path, "w", encoding="utf-8") as f:
        f.write(sample_file_content)

    try:
        # 1. Define Actions
        manipulate_file_action = Action(
            id="manipulate_file",
            name="Manipulate File",
            description="Performs various file operations such as listing, reading, and writing files.",
        )

        # 2. Configure the MCP Tool for File System
        # This requires `npm install -g @modelcontextprotocol/server-filesystem`
        file_system_tool = McpService(
            mcp_config=McpConfig(
                type=ToolGroupType.MCP,
                name="File System Tool Group",
                transport_config=McpTransportConfig(
                    transport_type=McpTransportType.STDIO,
                    command="npx",
                    args=["@modelcontextprotocol/server-filesystem", temp_dir],
                ),
            )
        )

        # 3. Register Actions and Tools with ToolkitService
        toolkit_service: ToolkitService = ToolkitService.instance
        toolkit_service.add_action(
            action=manipulate_file_action,
            next_actions=[],
            prev_actions=[],
        )
        toolkit_service.add_tool_group(
            tool_group=file_system_tool,
            connected_actions=[
                (manipulate_file_action, 1.0),
            ],
        )

        # 4. Configure Reasoner and Operator
        reasoner_service: ReasonerService = ReasonerService.instance
        reasoner = reasoner_service.get_reasoner()

        instruction = """You are an AI assistant that can interact with a file system."""
        operator_config = OperatorConfig(
            instruction=instruction,
            actions=[
                manipulate_file_action
            ],
            threshold=0.7,
            hops=3,
        )
        operator = Operator(config=operator_config)

        # 5. Define and Run the Job
        job_goal = "Create a new file named 'summary.txt' and write the content of 'sample.txt' into it, but prefixed with 'Summary: '."  # noqa: E501
        job = SubJob(
            id="job_file_system_ops",
            session_id="session_file_system_test",
            goal=job_goal,
            context=f"The current working directory is {temp_dir}.",
            original_job_id="test_original_job_id",
        )
        result = await operator.execute(reasoner=reasoner, job=job)

        print("-" * 20)
        print("✅ Operator execution completed!")
        print(f"📦 Final Result:\n{result.scratchpad}\n")

        # 6. Verify the result
        summary_path = Path(temp_dir) / "summary.txt"
        if summary_path.exists():
            print(f"✅ Verification successful: '{summary_path}' was created.")
            with open(summary_path, encoding="utf-8") as f:
                content = f.read()
                print(f"Content of summary.txt: {content}")
                expected_content = f"Summary: {sample_file_content}"
                assert content == expected_content
        else:
            print(f"❌ Verification failed: '{summary_path}' was not created.")

    finally:
        # Clean up the temporary directory
        print(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    asyncio.run(main())
