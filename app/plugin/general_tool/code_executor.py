from contextlib import redirect_stderr, redirect_stdout
import io
import traceback

from app.core.toolkit.tool import Tool


class CodeExecutorTool(Tool):
    """A tool to execute Python code snippets."""

    def __init__(self):
        super().__init__(
            name=self.execute_code.__name__,
            description=self.execute_code.__doc__ or "",
            function=self.execute_code,
        )

    async def execute_code(self, code: str) -> str:
        """Executes a given Python code snippet and returns the output or any errors.

        Args:
            code (str): The Python code snippet to execute.

        Returns:
            The output from the executed code (stdout/stderr and any exceptions).
        """
        shared_scope = {}
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, shared_scope)

            stdout_val = stdout_capture.getvalue()
            stderr_val = stderr_capture.getvalue()

            result = ""
            if stdout_val:
                result += f"--- STDOUT ---\n{stdout_val}\n"
            if stderr_val:
                result += f"--- STDERR ---\n{stderr_val}\n"
            if not result:
                result = "Code executed successfully with no output."

            return result

        except Exception:
            error_trace = traceback.format_exc()
            return f"--- EXECUTION FAILED ---\n{error_trace}"
