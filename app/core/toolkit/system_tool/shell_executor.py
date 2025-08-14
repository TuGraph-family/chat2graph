import asyncio
import traceback

from app.core.toolkit.tool import Tool


class ShellExecutorTool(Tool):
    """A tool to execute shell commands."""

    def __init__(self):
        super().__init__(
            name=self.execute_shell_command.__name__,
            description=self.execute_shell_command.__doc__ or "",
            function=self.execute_shell_command,
        )

    async def execute_shell_command(self, command: str) -> str:
        """Executes a given shell command and returns its output.

        Args:
            command (str): The shell command to execute (e.g., "pip install pandas").

        Returns:
            The combined output from stdout and stderr of the command.
        """
        try:
            # create a subprocess to run the command
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # wait for the command to complete and get the output
            stdout, stderr = await proc.communicate()

            result = ""
            if stdout:
                result += f"--- STDOUT ---\n{stdout.decode()}\n"
            if stderr:
                result += f"--- STDERR ---\n{stderr.decode()}\n"

            if proc.returncode != 0:
                result += f"--- Command exited with non-zero status: {proc.returncode} ---\n"

            if not result:
                return "Command executed successfully with no output."

            return result

        except Exception:
            error_trace = traceback.format_exc()
            return f"--- EXECUTION FAILED ---\n{error_trace}"
