from typing import Any

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.memory.reasoner_memory import BuiltinReasonerMemory, ReasonerMemory
from app.core.model.message import ModelMessage
from app.core.model.task import Task
from app.core.prompt.model_service import TASK_DESCRIPTOR_PROMPT_TEMPLATE
from app.core.prompt.reasoner import MONO_PROMPT_TEMPLATE
from app.core.reasoner.model_service import ModelService
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.core.reasoner.reasoner import Reasoner


class MonoModelReasoner(Reasoner):
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
        model_name: str = MessageSourceType.MODEL.value,
    ):
        super().__init__()

        self._model_name = model_name
        self._model: ModelService = ModelServiceFactory.create(
            model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE
        )

    async def infer(self, task: Task) -> str:
        """Infer by the reasoner.

        Args:
            task (Task): The task that needs to be reasoned.

        Returns:
            str: The conclusion and the final resultes of the inference.
        """
        # prepare the variables from the SystemEnv
        print_messages = SystemEnv.PRINT_REASONER_MESSAGES

        # set the system prompt
        sys_prompt = self._format_system_prompt(task=task)
        # logging
        if SystemEnv.PRINT_SYSTEM_PROMPT:
            print(f"\033[38;5;245mSystem:\n{sys_prompt}\033[0m\n")

        # trigger the reasoning process
        init_message = ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload=(
                "<shallow_thinking>\nEmpty\n</shallow_thinking>\n<action>\nEmpty\n</action>\n"
            ),
            job_id=task.job.id,
            step=1,
        )

        # init the memory
        reasoner_memory = self.init_memory(task=task)
        reasoner_memory.add_message(init_message)

        response = await self._model.generate(
            sys_prompt=sys_prompt,
            messages=reasoner_memory.get_messages(),
            tools=task.tools,
        )
        response.set_source_type(MessageSourceType.MODEL)
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
                            f"{i + 1}. {result.status.value} called function "
                            f"{result.func_name}:\n"
                            f"Call objective: {result.call_objective}\n"
                            f"Function Output: {result.output}"
                            for i, result in enumerate(func_call_results)
                        ]
                    )
                    + "\n</function_call_result>\033[0m\n"
                )

        return response.get_payload()

    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""
        # TODO: implement the update of the knowledge based on the reasoning process

    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process, used to debug the process."""
        # TODO: implement the evaluation of the inference process, to detect the issues and errors

    async def conclude(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclude the inference results."""
        return ""

    def _format_system_prompt(self, task: Task) -> str:
        """Set the system prompt."""
        task_description = task.operator_config.instruction if task.operator_config else ""

        # set the task context
        if task.insights:
            env_info = "\n".join([f"{insight}" for insight in task.insights])
        else:
            env_info = "No environment information provided in this round."
        if task.workflow_messages:
            scratchpad = "\n".join(
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

        reasoning_task = f"=====\nTASK:\n{task_description}\nCONTEXT:\n{task_context}\n====="

        if len(task.tools) > 0:
            func_description = "\n".join(
                [f"Function {tool.name}():\n\t{tool.description}\n" for tool in task.tools]
            )
        else:
            func_description = "No function calling in this round."

        if task.operator_config and task.operator_config.output_schema:
            output_schema = (
                "[Follow the final delivery example:]\n"
                + task.operator_config.output_schema.strip()
            )
        else:
            output_schema = ""

        return MONO_PROMPT_TEMPLATE.format(
            actor_name="AI Assistant",
            thinker_name=self._model_name,
            task=reasoning_task,
            functions=func_description,
            output_schema=output_schema,
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
