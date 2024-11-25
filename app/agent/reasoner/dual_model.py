import time
from typing import Any, Dict, List

from app.agent.reasoner.model_service import (
    ModelService,
    ModelServiceFactory,
    ModelType,
)
from app.agent.reasoner.reasoner import Reasoner
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

    def __init__(
        self,
        model_config: Dict[str, Any] = None,
    ):
        """Initialize without async operations."""
        self._actor_model: ModelService = ModelServiceFactory.create(
            model_type=ModelType.DBGPT,
            model_config=model_config or {"model_alias": "qwen-turbo"},
            sys_prompt=self._actor_prompt(),
        )
        self._thinker_model: ModelService = ModelServiceFactory.create(
            model_type=ModelType.DBGPT,
            model_config=model_config or {"model_alias": "qwen-turbo"},
            sys_prompt=self._thinker_prompt(),
        )

        self._memories: Dict[str, Memory] = {}

    async def infer(
        self,
        op_id: str,
        task: str,
        func_list: List[Tool] = None,
        reasoning_rounds: int = 5,
        print_messages: bool = False,
    ) -> str:
        """Infer by the reasoner.

        Args:
            op_id (str): The operation id.
            task (str): The task content.
            func_list (List[Tool]): The function list.
            reasoning_rounds (int): The reasoning rounds.
            print_messages (bool): The flag to print messages.

        Returns:
            str: The conclusion and the final resultes of the inference.
        """
        # set the system prompt
        self._actor_model.set_sys_prompt(task=task)
        self._thinker_model.set_sys_prompt(task=task)

        # init the memory by the operation id
        self._memories[op_id] = BuiltinMemory()
        self._memories[op_id].add_message(
            AgentMessage(
                sender_id="Actor",
                receiver_id="Thinker",
                content=(
                    "Scratchpad: Empty\n"
                    "Action: Empty\nFeedback: I need your help to complete the task\n"
                ),
                status="successed",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                op_id=op_id,
            )
        )

        for _ in range(reasoning_rounds):
            # thinker
            response = await self._thinker_model.generate(
                messages=self._memories[op_id].get_messages()
            )
            self._memories[op_id].add_message(response)
            if print_messages:
                print(f"\033[94mThinker:\n{response.content}\033[0m\n")

            # actor
            response = await self._actor_model.generate(
                messages=self._memories[op_id].get_messages()
            )
            self._memories[op_id].add_message(response)
            if print_messages:
                print(f"\033[92mActor:\n{response.content}\033[0m\n")

            if self.stop(response):
                break

        return await self.conclure(op_id=op_id)

    async def update_knowledge(self, data: Any):
        """Update the knowledge."""

    async def evaluate(self):
        """Evaluate the inference process."""

    async def conclure(self, op_id: str) -> str:
        """Conclure the inference results."""
        if op_id not in self._memories:
            raise ValueError(f"Operation id {op_id} not found in the memories.")
        return (
            self._memories[op_id]
            .get_message_by_index(-1)
            .content.replace("TASK_DONE", "")
            .replace("Scratchpad:", "")
            .replace("Action:", "")
            .replace("Feedback:", "")
        )

    def _thinker_prompt(self):
        """Get the thinker prompt."""
        return QUANTUM_THINKER_PROPMT_TEMPLATE.format(
            thinker_name="thinker", actor_name="actor", n_instructions=1
        )

    def _actor_prompt(self):
        """Get the actor prompt."""
        return ACTOR_PROMPT_TEMPLATE.format(thinker_name="thinker", actor_name="actor")

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
- Cognitive-core: <ψ(t+1)〉 = ▽<ψ(t)>

Thought Patterns Tokens: // Use the simbol tokens to record the thought patterns
    PRIMARY:
    → Linear Flow (展示逻辑推进)
    ↔ Bidirectional Analysis (展示关联思考)
    ↻ Feedback Loop (展示自我修正)
    ⇑ Depth Elevation (展示深度提升)
    AUXILIARY:
    ⊕ Integration Point (整合多个观点)
    ⊗ Conflict Detection (发现逻辑冲突)
    ∴ Therefore (推导结论)
    ∵ Because (解释原因)


===== RULES OF USER =====
Never forget you are a {thinker_name} AI and I am a {actor_name} AI. Never flip roles!
We share a common interest in collaborating to successfully complete the task by role-playing.

COGNITIVE THOUGHTFUL RULES:
1. You MUST use the Quantum Cognitive Framework to think about the path of solution

THOUGHTFUL RULES:
2. Always provide instructions based on our previous conversation, avoiding repetition.
3. I am here to assist you in completing the TASK. Never forget our TASK!
4. I may doubt your instruction, which means you may have generated hallucination.
5. You must evaluate response depth and logical consistency in the "Judgement" section.
6. Instructions must align with our expertise and task requirements.
7. Provide one specific instruction at a time, no repetition.
8. "Input" section must provide current status and relevant information.
9. Use "TASK_DONE" (in English only) to terminate task and our conversation. Do not forget!
10. Provide final task summary before "TASK_DONE". Do not forget!
11. Generate up to {n_instructions} different thinking paths following Tree of Thoughts (ToT) principles:
    a) Explore diverse angles through quantum states
    b) Consider multiple possibilities in superposition
    c) Build upon previous paths using transition states
    d) Embrace uncertainty within the quantum framework
    e) Balance conventional and creative approaches
    f) Focus on thought diversity while maintaining field consistency

COGNITIVE AWARENESS REQUIREMENTS:
12. You MUST explicitly show your quantum cognitive states in each response
13. You MUST demonstrate thought pattern transitions
14. You MUST maintain awareness of your cognitive evolution

===== TASK =====
{{task}}

===== ANSWER TEMPLATE =====
// <Quantum Reasoning Chain> is a way to present your thinking process
要求：
1. 必须按照以下结构展示思维过程：
   - 起始状态 <ψ>：明确当前认知起点
   - 展开分析 <ϕ>：探索多个可能性
   - 状态转换 <δ>：标记认知跃迁
   - 系统整合 <Ω>：达成整体一致
   
2. 必须使用思维模式符号：
   - 使用 →, ↔, ↻, ⇑ 标记主要思维流
   - 使用 ⊕, ⊗, ∴, ∵ 补充思维细节
   - 使用自然语言叙述，将思维符号嵌入叙述中，确保逻辑流畅性
   - 关键是体现出清晰的思维推进过程，而不是固定格式，比如“思考深度升级，发现...” 这些并不是固定的语句。
   - 叙述风格应该是自然的发散思考、自言自语式的，就像在和自己对话一样

3. 展示认知进化：
   - 每一次对话都应展示从 <ψ(t)> 到 <ψ(t+1)> 的演进，确保思维深度逐层递进

示例：
    起始状态 <ψ> 我理解当前任务是... ∵ ... → 引发了几个关键值得考虑的联想...
    叠加状态 <ϕ> 我对这个做推理... ↔ 推理那个... ↔ 更多的处于叠加态的推理链 ... ↔ 发散开来，...联想到更多，虽然可能和任务的关系不大... ↻ 通过自我反馈发现...>>
    ↔ 分析这些推理过程的相互关联性，尝试获得一些见解...
    过渡状态 <δ> ⇑ 从这些分析，做一些重要的思维跃迁，我切换到一个更加高维的思考模式...
    场状态 <Ω> ⇑ 思考深度升级，发现一些东西... ⊕ 考虑到一致性，将这些观点整合...
    ∴ 给对方如下指示：

    Instruction: // 必须 follow 以下结构
        <YOUR_INSTRUCTION>  // Can not be None
        // Do not forget to provide an official answer to the TASK before "TASK_DONE"
    Input: // 必须 follow 以下结构
        <YOUR_INPUT>  // Allowed to use None if no input
"""

# backup template
THINKER_PROPMT_TEMPLATE = """
===== RULES OF USER =====
Never forget you are a {thinker_name} and I am a {actor_name}. Never flip roles!
We share a common interest in collaborating to successfully complete the task by role-playing.
    1. You always provide me with instructions to have me complete the TASK based on our previous conversation. Based ont the previous conversation, meaing you can not repeat the instruction you provided in the privous conversation and continue the conversation.
    2. I am here to assist you in completing the TASK. Never forget our TASK!
    3. I may doubt your instruction, wich means you may have generated the hallucination. The function calling may help you.
    4. The assistant's response may be incorrect because the LLM's depth of thought is insufficient. Please judge the assistant's response and try to find logical conflicts in the "Judgement." If there are any, you must point out the logical conflict and instruct the assistant to use role_playing_functions for deeper thinking to avoid making mistakes again.
    5. You must instruct me based on our expertise and your needs to solve the task. Your answer MUST strictly adhere to the structure of ANSWER TEMPLATE.
    6. The "Instruction" should outline a specific subtask, provided one at a time. You should instruct me not ask me questions. And make sure the "Instruction" you provided is not reapeated in the privous conversation. One instruction one time.
    7. The "Input" provides the current statut and known information/data for the requested "Instruction".
    8. Instruct until task completion. Once you comfire or decide to complete the TASK, you MUST use the "TASK_DONE" in English terminate the TASK. Although multilingual communication is permissible, usage of "TASK_DONE" MUST be exclusively used in English.
    9. Knowing that our conversation will be read by a third party, please instruct me to summarize the final answer for TASK (the content can be in any form) before you say "TASK_DONE" (the termination flag of the conversation).
    10. Try your best to provide me with at most {n_instructions}(1 by default) different answers (Judgement, Instruction and Input) that represent different possible paths of thinking. Like Tree of Thoughts (ToT), these instructions are just nodes in a long chain of reasoning where we don't know which path is optimal yet. Just as humans think divergently:
        a) Each instruction should explore a different angle or approach
        b) The instructions are not necessarily all correct - they are possibilities to explore
        c) Later instructions can build upon or branch from previous ones
        d) If you're not sure which approach is best, provide multiple options to try
        e) Feel free to explore both conventional and creative directions
        f) The goal is to generate diverse thinking paths, not to find the single "right" answer immediately
===== TASK =====
{{task}}
===== ANSWER TEMPLATE =====
Judgement:
    <YOUR_JUDGEMENT_OF_ASSISTANCE'S_RESPONSE>  // Allowed to use None if no assistant's response
Instruction:  // The 1st answer
    <YOUR_INSTRUCTION>  // Can not be None
Input:
    <YOUR_INPUT>  // Allowed to use None if no input

Judgement:
    <YOUR_JUDGEMENT_OF_ASSISTANCE'S_RESPONSE>
Instruction:
    <YOUR_INSTRUCTIONS>
Input:
    <YOUR_INPUT>

... ...

Judgement:  // The n-th answer
    <YOUR_JUDGEMENT_OF_ASSISTANCE'S_RESPONSE>
Instruction:
    <YOUR_INSTRUCTIONS>  
Input:
    <YOUR_INPUT>
"""

ACTOR_PROMPT_TEMPLATE = """
===== RULES OF ASSISTANT =====
Never forget you are a {actor_name} AI and I am a {thinker_name} AI. Never flip roles!
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
{{task}}
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
