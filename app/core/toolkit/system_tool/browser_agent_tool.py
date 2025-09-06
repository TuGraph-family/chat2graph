from datetime import datetime
import json
from multiprocessing import Process, Queue
import os
from typing import Any, Dict

from app.core.model.message import HybridMessage
from app.core.toolkit.tool import Tool


class BrowserAgentTool(Tool):
    """A tool that loads and executes browser-based agents using the AgenticService.
    This tool can handle complex web browsing tasks by delegating to specialized web agents.
    """

    def __init__(self):
        super().__init__(
            name=self.assign_task_to_browser_agent.__name__,
            description=self.assign_task_to_browser_agent.__doc__ or "",
            function=self.assign_task_to_browser_agent,
        )

    async def assign_task_to_browser_agent(
        self,
        task_description: str,
        agent_config_path: str = "test/benchmark/gaia/gaia_browser_agent.yml",
        expert_name: str = "WebSurferExpert",
    ) -> Dict[str, Any]:
        """Delegate an independent or parallelizable web research / interaction task to a freshly instantiated "data twin" (self-cloned browser agent).

        MENTAL MODEL
        Think of this tool as: spawn(Self) -> Self' (an ephemeral, stateless but fully capable browser executor).
        You (Agent A) call this tool to create A' (a disposable clone) that:
          - Has the same browsing + multimodal capabilities.
          - Operates in isolation (no implicit shared scratchpad unless you encode context in task_description).
          - Returns only final structured output (no incremental streaming).
        DO NOT wait to "guide" A' step-by-step; instead package everything A' needs to succeed inside task_description.

        WHEN TO USE
        Use this tool if ANY of these are true:
          1. MAP / FAN-OUT: You must perform the same kind of lookup over a list (e.g., N cities, N authors, N product pages).
          2. PIPELINE STAGE IS SELF-CONTAINED: A sub-goal can be achieved without needing your ongoing reasoning state.
          3. LATENCY REDUCTION VIA PARALLELISM: Multiple independent web fetch + extract tasks can run “in parallel.”
          4. CONTEXT CLEANLINESS: You want to prevent contamination of your current reasoning trace with exploratory noise.
          5. TASK IS HIGH-VARIANCE / RETRYABLE: Safer to isolate (e.g., pages with possible blockers, paywalls, redirects).

        Do NOT use if:
          - You only need a trivial single value already visible in current page context.
          - The subtask requires tight iterative coordination with your current internal plan.
          - You have not yet decomposed the main goal properly (premature delegation).
          - You intend to stream intermediate steps (this call is batch-style).

        PATTERNS
        1. Map-Reduce Pattern:
           - Fan-out: Call N times: "For entity = X_i, gather attributes A,B,C with sources."
           - Reduce: After all results return, you aggregate & synthesize (outside this tool).
        2. Progressive Enrichment:
           - First wave: Collect base identifiers.
           - Second wave: For each identifier, call this tool to extract deeper metadata.
        3. Resilient Retry Envelope:
           - If a URL is volatile: encapsulate robust instructions (fallback search strategy, alternate domains).
        4. Scoped Historical Snapshot:
           - Provide explicit temporal constraints: "As of YYYY-MM-DD, verify archived version if page is dynamic."

        HOW TO CRAFT task_description
        Provide ONLY two top-level parts:

        TASK:
          A concise, unambiguous statement of the specific outcome required.

        TASK_CONTEXT:
          Essential supporting information the clone needs to execute correctly.
          Include only what is necessary:
            - Minimal background / clarifications
            - Required constraints (time validity, source priority, format)
            - Any identifiers / inputs / primary keys
            - Validation or cross-check expectations (if critical)

        Minimal Example:
        TASK: Extract latest official population and GDP (USD) for Copenhagen.
        TASK_CONTEXT: Use official statistical office first; fallback World Bank; cite sources; data year must be <= current year - 1; return JSON with fields: city, population_value, population_year, gdp_value_usd, gdp_year, sources[].


        Input Schema (Args):
        {
            "type": "object",
            "properties": {
                "task_description": { "type": "string", "description": "Complete self-contained delegation spec." },
                "agent_config_path": { "type": "string", "description": "Agent config file path.", "default": "test/benchmark/gaia/gaia_browser_agent.yml" },
                "expert_name": { "type": "string", "description": "Expert agent profile to bind.", "default": "WebSurferExpert" }
            },
            "required": ["task_description"]
        }
        """  # noqa: E501
        log_dir = "./.gaia_tmp"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(
            log_dir, f"browser_agent_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.log"
        )
        print(f"Logging browser agent output to: {log_file_path}")

        result_queue = Queue()
        process = Process(
            target=self._run_agent_in_subprocess,
            args=(agent_config_path, task_description, log_file_path, result_queue),
        )

        try:
            process.start()
            process.join()  # Wait for the subprocess to finish

            # get result from the queue
            subprocess_result_json = result_queue.get()
            subprocess_result = json.loads(subprocess_result_json)

            result = {
                "task_description": task_description,
                "expert_name": expert_name,
                "agent_config": agent_config_path,
                "log_file": log_file_path,
            }
            result.update(subprocess_result)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "task_description": task_description,
                "expert_name": expert_name,
                "agent_config": agent_config_path,
                "log_file": log_file_path,
            }
        finally:
            if process.is_alive():
                process.terminate()
                process.join()

    def _run_agent_in_subprocess(
        self,
        agent_config_path: str,
        task_description: str,
        log_file_path: str,
        result_queue: Queue,
    ) -> None:
        """Helper function to run the agentic service in a separate process.
        This isolates the agent's execution and allows for capturing its output.
        """
        try:
            import contextlib
            from datetime import datetime

            from app.core.model.message import TextMessage
            from app.core.sdk.agentic_service import AgenticService

            mas = AgenticService.load(agent_config_path)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            task_content = f"Current time: {current_time}\n\nTask: {task_description}"
            # TODO: improve the hardcoding of expert name "WebSurferExpert"
            user_message = TextMessage(payload=task_content, assigned_expert_name="WebSurferExpert")

            with open(log_file_path, "w", encoding="utf-8") as log_f:
                with contextlib.redirect_stdout(log_f), contextlib.redirect_stderr(log_f):
                    service_message = mas.session().submit(user_message).wait()

            if isinstance(service_message, TextMessage):
                result = {"result": service_message.get_payload(), "success": True}
            elif isinstance(service_message, HybridMessage):
                text_message = service_message.get_instruction_message()
                result = {"result": text_message.get_payload(), "success": True}
            else:
                result = {"result": str(service_message), "success": True}
            result_queue.put(json.dumps(result))
        except Exception as e:
            result = {"error": str(e), "error_type": type(e).__name__, "success": False}
            result_queue.put(json.dumps(result))