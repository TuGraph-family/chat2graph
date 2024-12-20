import time
from typing import Any, Callable, Dict, List, Optional

from app.agent.reasoner.model_service import ModelService
from app.agent.reasoner.model_service_factory import ModelServiceFactory
from app.agent.reasoner.reasoner import Reasoner
from app.agent.reasoner.task import Task
from app.commom.prompt.model_service import TASK_DESCRIPTOR_PROMPT_TEMPLATE
from app.commom.prompt.reasoner import MONO_PROMPT_TEMPLATE
from app.commom.system_env import SysEnvKey, SystemEnv
from app.commom.type import MessageSourceType
from app.memory.message import ModelMessage
from app.memory.reasoner_memory import BuiltinReasonerMemory, ReasonerMemory
from app.toolkit.action.action import Action


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
        self._model_name = model_name
        self._model: ModelService = ModelServiceFactory.create(
            platform_type=SystemEnv.platform_type(),
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
        print_messages = (
            SystemEnv.get(SysEnvKey.PRINT_REASONER_MESSAGES).lower() == "true"
        )

        # get the function list
        actions: List[Action] = task.actions or []
        funcs: List[Callable] = [
            tool.function for action in actions for tool in action.tools
        ]

        # set the system prompt
        sys_prompt = self._format_system_prompt(task=task, funcs=funcs)
        # logging
        print(f"\033[38;5;245mSystem:\n{sys_prompt}\033[0m\n")

        # trigger the reasoning process
        init_message = ModelMessage(
            source_type=MessageSourceType.MODEL,
            content=(
                "Scratchpad: Empty\n"
                "Action: Empty\nFeedback: I need your help to complete the task\n"
            ),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        # init the memory
        reasoner_memory = self.init_memory(task=task)
        reasoner_memory.add_message(init_message)

        response = await self._model.generate(
            sys_prompt=sys_prompt,
            messages=reasoner_memory.get_messages(),
            funcs=funcs,
        )
        response.set_source_type(MessageSourceType.MODEL)
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

        return response.get_payload()

    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""
        # TODO: implement the update of the knowledge based on the reasoning process

    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process, used to debug the process."""
        # TODO: implement the evaluation of the inference process, to detect the issues and errors

    async def conclure(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclure the inference results."""
        return ""

    def _format_system_prompt(
        self,
        task: Task,
        funcs: Optional[List[Callable]] = None,
    ) -> str:
        """Set the system prompt."""
        task_description = (
            task.operator_config.instruction if task.operator_config else ""
        )

        # set the task context
        if task.job.response and task.job.response.experience:
            experience = (
                "\n-----\nApplying historical execution insights "
                f"to optimize current task resolution.\n{task.job.response.experience}"
                "\n-----"
            )
        else:
            experience = ""
        if task.insights:
            env_info = "\n".join([f"{insight}" for insight in task.insights])
        else:
            env_info = "No environment information provided in this round."
        if task.workflow_messages:
            scratchpad = "\n".join([
                f"{workflow_message.scratchpad}"
                for workflow_message in task.workflow_messages
            ])
        else:
            scratchpad = "No scratchpad provided in this round."
        action_rels = "\n".join([
            f"[{action.name}: {action.description}] -next-> " for action in task.actions
        ])

        task_context = TASK_DESCRIPTOR_PROMPT_TEMPLATE.format(
            context=task.job.context + experience,
            env_info=env_info,
            knowledge=task.knowledge,
            action_rels=action_rels,
            scratchpad=scratchpad,
        )

        reasoning_task = (
            f"=====\nTASK:\n{task_description}\nCONTEXT:\n{task_context}\n====="
        )

        if funcs:
            func_description = "\n".join([
                f"Function: {func.__name__}()\n{func.__doc__}\n" for func in funcs
            ])
        else:
            func_description = "No function calling in this round."

        if task.operator_config and task.operator_config.output_schema:
            output_schema = "\n".join([
                "\t    " + schema
                for schema in (
                    f"[Follow the final delivery example:]\n{task.operator_config.output_schema}"
                ).split("\n")
            ])
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
