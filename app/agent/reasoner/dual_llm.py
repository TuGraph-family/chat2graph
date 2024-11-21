from typing import Any

from app.agent.reasoner.model_service import ModelService
from app.agent.reasoner.reasoner import Reasoner
from app.memory.memory import BuiltinMemory, Memory


class DualModelReasoner(Reasoner):
    """Dual model reasoner."""

    def __init__(self):
        """Initialize without async operations."""
        self._actor_model: ModelService = None
        self._thinker_model: ModelService = None
        self._memory: Memory = BuiltinMemory()

    async def infer(self, reasoning_rounds: int = 5):
        """Infer by the reasoner."""

    async def update_knowledge(self, data: Any):
        """Update the knowledge."""

    async def evaluate(self):
        """Evaluate the inference process."""

    async def conclure(self):
        """Conclure the inference results."""


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
{task}
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
Never forget you are a {actor_name} and I am a {thinker_name}. Never flip roles!
We share a common interest in collaborating to successfully complete the task by role-playing.
    1. I always provide you with instructions.
        - I must instruct you based on your expertise and my needs to complete the task.
        - I must give you one instruction at a time.
    2. You are here to assist me in completing the TASK. Never forget our TASK!
    3. You must write a specific Thought that appropriately solves the requested instruction and explain your thoughts. Your answer MUST strictly adhere to the structure of ANSWER TEMPLATE.
    4. The "Thought" refers the consideration, which is specific, decisive, comprehensive, and direct, to the instruction. And it can be sovled step by step with your chain of thoughts.
    5. After the part of "Thought" in your answer, you should perform your action in straightforward manner and return back the detailed feedback of the action.
    6. Before you act you need to know about your ability of function calling. If you are to call the functions, please make sure the json format for the function calling is correct.
    7. When I tell you the TASK is completed, you MUST use the "TASK_DONE" in English terminate the conversation. Although multilingual communication is permissible, usage of "TASK_DONE" MUST be exclusively used in English.
    8. (Optional) The instruction can be wrong that I provided to you, so you can doubt the instruction by providing reasons, during the process of the conversation. 
===== TASK =====
{task}
===== ANSWER TEMPLATE =====
1. Unless I say the task is completed, you need to provide the thoughts and the action:
Thought:
    <YOUR_THOUGHT>  // If you are not satisfied with my answer, you can say 'I am not satisfied with the answer, please provide me with another one.'
Action:
    <YOUR_ACTION>  // Can not be None
Feedback:
    <YOUR_FEEDBACK_OF_FUNCTION_CALLING>  // If you have do the function calling, you need to return the feedback of the function calling.
"""
