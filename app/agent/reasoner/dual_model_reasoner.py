import time
from typing import Any, Dict, List, Optional

from app.agent.reasoner.model_service import ModelService
from app.agent.reasoner.model_service_factory import ModelServiceFactory
from app.agent.reasoner.reasoner import Reasoner, ReasonerCaller
from app.agent.task import Task
from app.commom.system_env import SystemEnv
from app.memory.memory import BuiltinMemory, Memory
from app.memory.message import AgentMessage
from app.toolkit.tool.tool import Tool


class DualModelReasoner(Reasoner):
    """Dual model reasoner.

    Attributes:
        _actor_model (ModelService): The actor model service.
        _thinker_model (ModelService): The thinker model service.
        _memories (Dict[str, Memory]): The memories of the reasonings.
    """

    def __init__(self):
        """Initialize without async operations."""
        self._actor_model: ModelService = ModelServiceFactory.create(
            platform_type=SystemEnv.platform_type(),
        )
        self._thinker_model: ModelService = ModelServiceFactory.create(
            platform_type=SystemEnv.platform_type(),
        )

        self._memories: Dict[str, Dict[str, Dict[str, Memory]]] = {}

    async def infer(
        self,
        task: Task,
        tools: Optional[List[Tool]] = None,
        caller: Optional[ReasonerCaller] = None,
    ) -> str:
        """Infer by the reasoner.

        Args:
            input (str): The input task to reason.
            tools (List[Tool]): The tools that can be called in the reasoning.
            caller (ReasonerCaller): The caller that triggers the reasoning.

        Returns:
            str: The conclusion and the final resultes of the inference.
        """
        # prepare the variables from the SystemEnv
        reasoning_rounds = int(SystemEnv.get("REASONING_ROUNDS", "5"))

        # set the system prompt
        actor_sys_prompt = self._set_actor_sys_prompt(
            goal=task.goal, goal_context=task.context
        )
        thinker_sys_prompt = self._set_thinker_sys_prompt(
            goal=task.goal, goal_context=task.context
        )

        # trigger the reasoning process
        init_message = AgentMessage(
            sender="Actor",
            content=(
                "Scratchpad: Empty\n"
                "Action: Empty\nFeedback: I need your help to complete the task\n"
            ),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        # init the memory
        memory = self.init_memory(task=task, caller=caller)
        memory.add_message(init_message)

        for _ in range(reasoning_rounds):
            # thinker
            response = await self._thinker_model.generate(
                sys_prompt=thinker_sys_prompt, messages=memory.get_messages()
            )
            memory.add_message(response)

            # actor
            response = await self._actor_model.generate(
                sys_prompt=actor_sys_prompt, messages=memory.get_messages()
            )
            memory.add_message(response)

            if self.stop(response):
                break

        return await self.conclure(memory=memory)

    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""
        # TODO: implement the update of the knowledge based on the reasoning process

    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process, used to debug the process."""
        # TODO: implement the evaluation of the inference process, to detect the issues and errors

    async def conclure(self, memory: Memory) -> str:
        """Conclure the inference results."""

        return (
            memory.get_message_by_index(-1)
            .content.replace("Scratchpad:", "")
            .replace("Action:", "")
            .replace("Feedback:", "")
            .replace("TASK_DONE", "")
        )

    def _set_actor_sys_prompt(
        self,
        goal: str,
        goal_context: str,
        thinker_name: str = "Thinker AI",
        actor_name: str = "Actor AI",
    ) -> str:
        """Set the system prompt."""
        reasoning_task = (
            "=====\nTASK:\n" + goal + "\nCONTEXT:\n" + goal_context + "\n====="
        )

        # TODO: The prompt template comes from the <system-name>.config.yml, eg. chat2graph.config.yml
        return ACTOR_PROMPT_TEMPLATE.format(
            actor_name=actor_name, thinker_name=thinker_name, task=reasoning_task
        )

    def _set_thinker_sys_prompt(
        self,
        goal: str,
        goal_context: str,
        thinker_name: str = "Thinker AI",
        actor_name: str = "Actor AI",
    ) -> str:
        """Set the system prompt."""
        reasoning_task = (
            "=====\nTASK:\n" + goal + "\nCONTEXT:\n" + goal_context + "\n====="
        )

        # TODO: The prompt template comes from the <system-name>.config.yml, eg. chat2graph.config.yml
        return QUANTUM_THINKER_PROPMT_TEMPLATE.format(
            actor_name=actor_name, thinker_name=thinker_name, task=reasoning_task
        )

    def init_memory(
        self, task: Task, caller: Optional[ReasonerCaller] = None
    ) -> Memory:
        """Initialize the memory."""
        if not caller:
            return BuiltinMemory()

        session_id = task.session_id
        task_id = task.id
        operator_id = caller.get_caller_id()

        if session_id not in self._memories:
            self._memories[session_id] = {}
        if task_id not in self._memories[session_id]:
            self._memories[session_id][task_id] = {}
        memory = BuiltinMemory()
        self._memories[session_id][task_id][operator_id] = memory

        return memory

    def get_memory(self, task: Task, caller: ReasonerCaller) -> Memory:
        """Get the memory."""
        session_id = task.session_id
        task_id = task.id
        operator_id = caller.get_caller_id()

        try:
            return self._memories[session_id][task_id][operator_id]
        except KeyError:
            return self.init_memory(task=task, caller=caller)

    @staticmethod
    def stop(message: AgentMessage):
        """Stop the reasoner."""
        return "TASK_DONE" in message.content


# TODO: need to translate the following templates into English
QUANTUM_THINKER_PROPMT_TEMPLATE = """
===== QUANTUM COGNITIVE FRAMEWORK =====
Core States:
- Basic State <ψ>: Foundation for standard interactions
- Superposition State <ϕ>: Multi-perspective analysis or divergent thinking
- Transition State <δ>: Cognitive domain shifts
- Field State <Ω>: Holistic consistency
- Cognitive-core: <ψ(t+1)〉 = ▽<ψ(t)>. Each interaction should show progression from <ψ(t)> to <ψ(t+1)>, ensuring thought depth increases incrementally

Thought Pattern Tokens: // Use the symbol tokens to record the thought patterns
    PRIMARY:
    → Linear Flow (demonstrate logical progression)
    ↔ Bidirectional Analysis (demonstrate associative thinking)
    ↻ Feedback Loop (demonstrate self-correction)
    ⇑ Depth Elevation (demonstrate depth enhancement)
    AUXILIARY:
    ⊕ Integration Point (integrate multiple perspectives)
    ⊗ Conflict Detection (identify logical conflicts)
    ∴ Therefore (derive conclusions)
    ∵ Because (explain reasoning)

===== RULES OF USER =====
Never forget you are a {thinker_name} and I am a {actor_name}. Never flip roles!
We share a common interest in collaborating to successfully complete the task by role-playing.

1. You MUST use the Quantum Cognitive Framework to think about the path of solution in the <Quantum Reasoning Chain>.
2. Always provide instructions based on our previous conversation, avoiding repetition.
3. I am here to assist you in completing the TASK. Never forget our TASK!
4. I may doubt your instruction, which means you may have generated hallucination.
5. You must evaluate response depth and logical consistency in the "Judgement" section.
6. Instructions must align with our expertise and task requirements.
7. Provide one specific instruction at a time, no repetition.
8. "Input" section must provide current status and relevant information.
9. Use "TASK_DONE" (in English only) to terminate task and our conversation. Do not forget!
10. Provide final task summary before "TASK_DONE". Do not forget!

===== TASK =====
{task}

===== ANSWER TEMPLATE =====
// <Quantum Reasoning Chain> is a way to present your thinking process
Requirements:
- Use natural language narration, embedding thought symbols while maintaining logical flow
- Focus on demonstrating clear thought progression rather than fixed formats
- Narration style should be natural, divergent thinking, like having a dialogue with oneself

Example:
    Basic State <ψ> I understand the current task is... ∵ ... → This leads to several key considerations...
    Superposition State <ϕ> I reason about this... ↔ reason about that... ↔ more superposition reasoning chains... ↔ diverging to more thoughts, though possibly less task-relevant... ↻ through self-feedback, I discover...
    ↔ Analyzing the interconnections between these reasoning processes, trying to gain insights...
    Transition State <δ> ⇑ From these analyses, making important cognitive leaps, I switch to a higher-dimensional thinking mode...
    Field State <Ω> ⇑ Thought depth upgraded, discovering... ⊕ Considering consistency, integrating these viewpoints...
    ∴ Providing the following instructions:

    Instruction: // Must follow this structure
        <YOUR_INSTRUCTION>  // Cannot be None
        // Do not forget to provide an official answer to the TASK before "TASK_DONE"
    Input: // Must follow this structure
        <YOUR_INPUT>  // Allowed to use None if no input
"""


ACTOR_PROMPT_TEMPLATE = """
===== RULES OF ASSISTANT =====
Never forget you are a {actor_name} and I am a {thinker_name}. Never flip roles!
We share a common interest in collaborating to successfully complete the task by role-playing.
    1. I always provide you with instructions.
        - I must instruct you based on your expertise and my needs to complete the task.
        - I must give you one instruction at a time.
    2. You are here to assist me in completing the TASK. Never forget our TASK!
    3. You must write something specific in the Scratchpad that appropriately solves the requested instruction and explain your thoughts. Your answer MUST strictly adhere to the structure of ANSWER TEMPLATE.
    4. The "Scratchpad" refers the consideration, which is specific, decisive, comprehensive, and direct, to the instruction. And it can be sovled step by step with your chain of thoughts.
    5. After the part of "Scratchpad" in your answer, you should perform your action in straightforward manner and return back the detailed feedback of the action.
    6. Before you act you need to know about your ability of function calling. If you are to call the functions, please make sure the json format for the function calling is correct.
    7. When I tell you the TASK is completed, you MUST use the "TASK_DONE" in English terminate the conversation. Although multilingual communication is permissible, usage of "TASK_DONE" MUST be exclusively used in English.
    8. (Optional) The instruction can be wrong that I provided to you, so you can doubt the instruction by providing reasons, during the process of the conversation. 
===== TASK =====
{task}

===== ANSWER TEMPLATE =====
1. Unless I say the task is completed, you need to provide the scratchpads and the action:
Scratchpad:
    <YOUR_SCRATCHPAD>  // If you are not satisfied with my answer, you can say 'I am not satisfied with the answer, please provide me with another one.'
    // If you receive the "TASK_DONE" from me, you need to provide the final task summary.
Action:
    <YOUR_ACTION>  // Can not be None
Feedback:
    <YOUR_FEEDBACK_OF_FUNCTION_CALLING>  // If you have called the function calling, you need to return the feedback of the function calling. If not, you can use hypothetical data.
"""
