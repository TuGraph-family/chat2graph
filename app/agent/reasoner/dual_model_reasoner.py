import re
import time
from typing import Any, Callable, Dict, List, Optional

from app.agent.reasoner.model_service import ModelService
from app.agent.reasoner.model_service_factory import ModelServiceFactory
from app.agent.reasoner.reasoner import Reasoner, ReasonerCaller
from app.agent.workflow.operator.task import Task
from app.commom.prompt import (
    ACTOR_PROMPT_TEMPLATE,
    QUANTUM_THINKER_PROPMT_TEMPLATE,
)
from app.commom.system_env import SysEnvKey, SystemEnv
from app.commom.type import MessageSourceType
from app.memory.message import AgentMessage
from app.memory.reasoner_memory import BuiltinReasonerMemory, ReasonerMemory
from app.toolkit.tool.tool import Tool


class DualModelReasoner(Reasoner):
    """Dual model reasoner.

    Attributes:
        _actor_name (str): The name of the actor.
        _thinker_name (str): The name of the thinker.
        _actor_model (ModelService): The actor model service.
        _thinker_model (ModelService): The thinker model service.
        _memories (Dict[str, ReasonerMemory]): The memories of the reasonings.
    """

    def __init__(
        self,
        actor_name: str = MessageSourceType.ACTOR.value,
        thinker_name: str = MessageSourceType.THINKER.value,
    ):
        self._actor_name = actor_name
        self._thinker_name = thinker_name
        self._actor_model: ModelService = ModelServiceFactory.create(
            platform_type=SystemEnv.platform_type(),
        )
        self._thinker_model: ModelService = ModelServiceFactory.create(
            platform_type=SystemEnv.platform_type(),
        )

        self._memories: Dict[str, Dict[str, Dict[str, ReasonerMemory]]] = {}

    async def infer(
        self,
        task: Task,
        tools: Optional[List[Tool]] = None,
        caller: Optional[ReasonerCaller] = None,
    ) -> str:
        """Infer by the reasoner.

        Args:
            task (Task): The task that needs to be reasoned.
            tools (List[Tool]): The tools that can be called in the reasoning.
            caller (ReasonerCaller): The caller that triggers the reasoning.

        Returns:
            str: The conclusion and the final resultes of the inference.
        """
        # logging
        # TODO: use standard logging instead of print
        print(f"Operator starts reasoning for task:\n{task.task_description}")
        print(f"Operator inference Context:\n{task.task_context}")
        print(f"Operator inference Output Schema:\n{task.output_schema}")

        # prepare the variables from the SystemEnv
        reasoning_rounds = int(SystemEnv.get(SysEnvKey.REASONING_ROUNDS))
        print_messages = (
            SystemEnv.get(SysEnvKey.PRINT_REASONER_MESSAGES).lower() == "true"
        )

        # get the function list
        funcs: List[Callable] = [tool.function for tool in tools] if tools else []

        # set the system prompt
        actor_sys_prompt = self._format_actor_sys_prompt(
            task=task,
            funcs=funcs,
        )
        thinker_sys_prompt = self._format_thinker_sys_prompt(task=task)

        # trigger the reasoning process
        init_message = AgentMessage(
            source_type=MessageSourceType.ACTOR,
            content=(
                "Scratchpad: Empty\n"
                "Action: Empty\nFeedback: I need your help to complete the task\n"
            ),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        # init the memory
        reasoner_memory = self.init_memory(task=task, caller=caller)
        reasoner_memory.add_message(init_message)

        for _ in range(reasoning_rounds):
            # thinker
            response = await self._thinker_model.generate(
                sys_prompt=thinker_sys_prompt, messages=reasoner_memory.get_messages()
            )
            response.set_source_type(MessageSourceType.THINKER)
            reasoner_memory.add_message(response)

            # TODO: use standard logging instead of print
            if print_messages:
                print(f"\033[94mThinker:\n{response.get_payload()}\033[0m\n")

            # actor
            response = await self._actor_model.generate(
                sys_prompt=actor_sys_prompt,
                messages=reasoner_memory.get_messages(),
                funcs=funcs,
            )
            response.set_source_type(MessageSourceType.ACTOR)
            reasoner_memory.add_message(response)

            # TODO: use standard logging instead of print
            if print_messages:
                print(f"\033[92mActor:\n{response.get_payload()}\033[0m\n")
                func_call_results = response.get_function_calls()
                if func_call_results:
                    print(
                        "\033[92m"
                        + "\n".join([
                            f"{i + 1}. {result.status} called function "
                            f"{result.func_name}:\n"
                            f"Call objective: {result.call_objective}\n"
                            f"Function Output: {result.output}"
                            for i, result in enumerate(func_call_results)
                        ])
                        + "\033[0m\n"
                    )

            if self.stop(response):
                break

        return await self.conclure(reasoner_memory=reasoner_memory)

    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""
        # TODO: implement the update of the knowledge based on the reasoning process

    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process, used to debug the process."""
        # TODO: implement the evaluation of the inference process, to detect the issues and errors

    async def conclure(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclure the inference results."""

        content = reasoner_memory.get_message_by_index(-1).get_payload()

        # find DELIVERABLE content
        match = re.search(r"<DELIVERABLE>:\s*(.*)", content, re.DOTALL)

        # If match found, process and return the content
        if match:
            deliverable_content = match.group(1)
            return (
                deliverable_content.replace("<Scratchpad>:", "")
                .replace("<Action>:", "")
                .replace("<Feedback>:", "")
                .replace("TASK_DONE", "")
            )
        return (
            content.replace("<Scratchpad>:", "")
            .replace("<Action>:", "")
            .replace("<Feedback>:", "")
            .replace("TASK_DONE", "")
        )

    def _format_actor_sys_prompt(
        self,
        task: Task,
        funcs: Optional[List[Callable]] = None,
    ) -> str:
        """Set the system prompt."""
        reasoning_task = (
            f"=====\nTASK:\n{task.task_description}\n"
            f"CONTEXT:\n{task.task_context}\n====="
        )

        if funcs:
            func_description = "\n".join([
                f"Function: {func.__name__}()\n{func.__doc__}\n" for func in funcs
            ])
        else:
            func_description = "No function calling in this round."

        if task.output_schema:
            output_schema = "\n".join([
                "\t    " + schema
                for schema in (
                    f"[Follow the final delivery example:]\n{task.output_schema}"
                ).split("\n")
            ])
        else:
            output_schema = ""

        # TODO: The prompt template comes from the <system-name>.config.yml, eg. chat2graph.config.yml
        return ACTOR_PROMPT_TEMPLATE.format(
            actor_name=self._actor_name,
            thinker_name=self._thinker_name,
            task=reasoning_task,
            functions=func_description,
            output_schema=output_schema,
        )

    def _format_thinker_sys_prompt(
        self,
        task: Task,
    ) -> str:
        """Set the system prompt."""
        reasoning_task = (
            "=====\nTASK:\n"
            + task.task_description
            + "\nCONTEXT:\n"
            + task.task_context
            + "\n====="
        )

        # TODO: The prompt template comes from the <system-name>.config.yml, eg. chat2graph.config.yml
        return QUANTUM_THINKER_PROPMT_TEMPLATE.format(
            actor_name=self._actor_name,
            thinker_name=self._thinker_name,
            task=reasoning_task,
        )

    def init_memory(
        self, task: Task, caller: Optional[ReasonerCaller] = None
    ) -> ReasonerMemory:
        """Initialize the memory."""
        if not caller:
            return BuiltinReasonerMemory()

        session_id = task.get_session_id()
        job_id = task.get_job_id()
        operator_id = caller.get_id()

        if session_id not in self._memories:
            self._memories[session_id] = {}
        if job_id not in self._memories[session_id]:
            self._memories[session_id][job_id] = {}
        reasoner_memory = BuiltinReasonerMemory()
        self._memories[session_id][job_id][operator_id] = reasoner_memory

        return reasoner_memory

    def get_memory(self, task: Task, caller: ReasonerCaller) -> ReasonerMemory:
        """Get the memory."""
        session_id = task.get_session_id()
        job_id = task.get_job_id()
        operator_id = caller.get_id()

        try:
            return self._memories[session_id][job_id][operator_id]
        except KeyError:
            return self.init_memory(task=task, caller=caller)

    @staticmethod
    def stop(message: AgentMessage) -> bool:
        """Stop the reasoner."""
        return "TASK_DONE" in message.get_payload()
