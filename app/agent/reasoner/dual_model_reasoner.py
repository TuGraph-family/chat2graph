import re
import time
from typing import Any, Dict

from app.agent.reasoner.model_service import ModelService
from app.agent.reasoner.model_service_factory import ModelServiceFactory
from app.agent.reasoner.reasoner import Reasoner
from app.agent.reasoner.task import Task
from app.core.prompt.model_service import TASK_DESCRIPTOR_PROMPT_TEMPLATE
from app.core.prompt.reasoner import ACTOR_PROMPT_TEMPLATE, QUANTUM_THINKER_PROPMT_TEMPLATE
from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.memory.message import ModelMessage
from app.core.memory.reasoner_memory import BuiltinReasonerMemory, ReasonerMemory


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
            platform_type=SystemEnv.PLATFORM_TYPE
        )
        self._thinker_model: ModelService = ModelServiceFactory.create(
            platform_type=SystemEnv.PLATFORM_TYPE
        )

        self._memories: Dict[str, Dict[str, Dict[str, ReasonerMemory]]] = {}

    async def infer(self, task: Task) -> str:
        """Infer by the reasoner.

        Args:
            task (Task): The task that needs to be reasoned.

        Returns:
            str: The conclusion and the final resultes of the inference.
        """
        # prepare the variables from the SystemEnv
        reasoning_rounds = SystemEnv.REASONING_ROUNDS
        print_messages = SystemEnv.PRINT_REASONER_MESSAGES

        # set the system prompt
        actor_sys_prompt = self._format_actor_sys_prompt(task=task)
        thinker_sys_prompt = self._format_thinker_sys_prompt(task=task)
        if SystemEnv.PRINT_SYSTEM_PROMPT:
            print(f"\033[38;5;245mSystem:\n{actor_sys_prompt}\033[0m\n")

        # trigger the reasoning process
        init_message = ModelMessage(
            source_type=MessageSourceType.ACTOR,
            payload=(
                "<scratchpad>\nEmpty\n</scratchpad>\n"
                "<action>\nEmpty\n</action>\n"
                "<feedback>\nNo feadback\n</feedback>\n"
            ),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        # init the memory
        reasoner_memory = self.init_memory(task=task)
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
                tools=task.tools,
            )
            response.set_source_type(MessageSourceType.ACTOR)
            reasoner_memory.add_message(response)

            # TODO: use standard logging instead of print
            if print_messages:
                print(f"\033[92mActor:\n{response.get_payload()}\033[0m\n")
                func_call_results = response.get_function_calls()
                if func_call_results:
                    print(
                        "\033[92m<function_call_result>\n"
                        + "\n".join(
                            [
                                f"{i + 1}. {result.status} called function "
                                f"{result.func_name}:\n"
                                f"Call objective: {result.call_objective}\n"
                                f"Function Output: {result.output}"
                                for i, result in enumerate(func_call_results)
                            ]
                        )
                        + "\n</function_call_result>\033[0m\n"
                    )

            if self.stop(response):
                break

        return await self.conclude(reasoner_memory=reasoner_memory)

    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""
        # TODO: implement the update of the knowledge based on the reasoning process

    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process, used to debug the process."""
        # TODO: implement the evaluation of the inference process, to detect the issues and errors

    async def conclude(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclude the inference results."""

        content = reasoner_memory.get_message_by_index(-1).get_payload()

        # find DELIVERABLE content
        match = re.search(r"<DELIVERABLE>\s*(.*?)\s*</DELIVERABLE>", content, re.DOTALL)

        # If match found, process and return the content
        if match:
            deliverable_content = match.group(1)
            reasoner_output = (
                deliverable_content.replace("<scratchpad>", "")
                .replace("</scratchpad>", "")
                .replace("<action>", "")
                .replace("</action>", "")
                .replace("<feedback>", "")
                .replace("</feedback>", "")
                .replace("</DELIVERABLE>", "")
                .replace("TASK_DONE", "")
            )
        else:
            reasoner_output = (
                content.replace("<scratchpad>", "")
                .replace("</scratchpad>", "")
                .replace("<action>", "")
                .replace("</action>", "")
                .replace("<feedback>", "")
                .replace("</feedback>", "")
                .replace("</DELIVERABLE>", "")
                .replace("TASK_DONE", "")
            )
        if SystemEnv.PRINT_REASONER_OUTPUT:
            print(f"\033[38;5;245mReasoner:\n{reasoner_output}\033[0m\n")

        return reasoner_output

    def _format_actor_sys_prompt(self, task: Task) -> str:
        """Set the system prompt."""
        # set the task description
        task_description = task.operator_config.instruction if task.operator_config else ""

        # set the task context
        if task.insights:
            env_info = "\n".join([f"{insight}" for insight in task.insights])
        else:
            env_info = "No environment information provided in this round."
        if task.workflow_messages:
            scratchpad = "Here is the previous job execution's output:\n" + "\n".join(
                [f"{workflow_message.scratchpad}" for workflow_message in task.workflow_messages]
            )
        else:
            scratchpad = "No scratchpad provided in this round."
        action_rels = "\n".join(
            [f"[{action.name}: {action.description}] -next-> " for action in task.actions]
        )
        task_context = TASK_DESCRIPTOR_PROMPT_TEMPLATE.format(
            context=task.job.context,
            env_info=env_info,
            knowledge=task.knowledge,
            action_rels=action_rels,
            scratchpad=scratchpad,
            lesson=task.lesson or "No lesson learned in this round.",
        )

        # set the reasoning task
        reasoning_task = f"=====\nTASK:\n{task_description}\nCONTEXT:\n{task_context}\n====="

        # set the function docstrings
        if len(task.tools) > 0:
            func_description = "\n".join(
                [f"Function {tool.name}():\n\t{tool.description}\n" for tool in task.tools]
            )
        else:
            func_description = "No function calling in this round."

        if task.operator_config and task.operator_config.output_schema:
            output_schema = "\n".join(
                [
                    "\t    " + schema
                    for schema in (
                        "[Follow the final delivery example:]\n"
                        f"{task.operator_config.output_schema.strip()}"
                    ).split("\n")
                ]
            )
        else:
            output_schema = ""

        # TODO: The prompt template comes from the <system-name>.config.yaml
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
        # set the task description
        task_description = task.operator_config.instruction if task.operator_config else ""
        # set the task context
        if task.insights:
            env_info = "\n".join([f"{insight}" for insight in task.insights])
        else:
            env_info = "No environment information provided in this round."
        if task.workflow_messages:
            scratchpad = "\n".join(
                [
                    f"{str(workflow_message.scratchpad)}"
                    for workflow_message in task.workflow_messages
                ]
            )
        else:
            scratchpad = "No scratchpad provided in this round."
        action_rels = "\n".join(
            [f"[{action.name}: {action.description}] -next-> " for action in task.actions]
        )
        task_context = TASK_DESCRIPTOR_PROMPT_TEMPLATE.format(
            context=task.job.context,
            env_info=env_info,
            knowledge=task.knowledge,
            action_rels=action_rels,
            scratchpad=scratchpad,
            lesson=task.lesson or "No lesson learned in this round.",
        )

        # set the reasoning task
        reasoning_task = f"=====\nTASK:\n{task_description}\nCONTEXT:\n{task_context}\n====="

        # TODO: The prompt template comes from the <system-name>.config.yaml
        return QUANTUM_THINKER_PROPMT_TEMPLATE.format(
            actor_name=self._actor_name,
            thinker_name=self._thinker_name,
            task=reasoning_task,
        )

    def init_memory(self, task: Task) -> ReasonerMemory:
        """Initialize the memory."""
        if not task.operator_config:
            return BuiltinReasonerMemory()

        session_id = task.job.session_id
        job_id = task.job.id
        operator_id = task.operator_config.id

        if session_id not in self._memories:
            self._memories[session_id] = {}
        if job_id not in self._memories[session_id]:
            self._memories[session_id][job_id] = {}
        reasoner_memory = BuiltinReasonerMemory()
        self._memories[session_id][job_id][operator_id] = reasoner_memory

        return reasoner_memory

    def get_memory(self, task: Task) -> ReasonerMemory:
        """Get the memory."""
        session_id = task.job.session_id
        job_id = task.job.id

        try:
            assert task.operator_config
            operator_id = task.operator_config.id
            return self._memories[session_id][job_id][operator_id]
        except (KeyError, AssertionError, AttributeError):
            return self.init_memory(task=task)

    @staticmethod
    def stop(message: ModelMessage) -> bool:
        """Stop the reasoner."""
        # TODO: fix the stop condition
        return "DELIVERABLE" in message.get_payload()
