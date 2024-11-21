from typing import List

from app.agent.reasoner.dual_llm import DualModelReasoner
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit


class Operator:
    """Operator is a sequence of actions and tools that need to be executed."""

    def __init__(self):
        self._actions: List[Action] = []

        self._embedding_vector: List[float] = None  # embedding vector of context
        self._toolkit: Toolkit = None

        self.set_actions_and_tools()

    def format_operation_prompt(self, task: str, context: str, scratchpad: str) -> str:
        """Format the operation prompt."""
        return OPERATION_PT.format(
            task=task,
            context=context,
            knowledge=self.get_knowledge(),
            action_rels=self.get_action_rels(),
            tool_docstrings=self.get_tool_docstrings(),
            scratchpad=scratchpad,
        )

    async def execute(self, reasoner: DualModelReasoner):
        """Execute the operator by LLM client."""

    async def get_knowledge(self):
        """Get the knowledge from the knowledge base."""

    async def set_actions_and_tools(self) -> None:
        """Get the actions from the toolkit."""
        self._actions = await self._toolkit.recommend_actions_and_tools()

    def get_action_rels(self) -> str:
        """Get the action relationships from the toolkit."""
        action_rels = "\n".join([
            f"[{action.name}] -next-> [{str(action.next_action_names)}]"
            for action in self._actions
        ])
        return action_rels

    def get_tool_docstrings(self) -> str:
        """Get the tool names and docstrings from the toolkit."""
        _tools: List[Tool] = []
        tool_docstrings = ""
        for action in self._actions:
            for tool in action.tools:
                if tool not in _tools:
                    tool_docstrings += (
                        f"func {tool.function.__name__}:\n{tool.function.__doc__}\n"
                    )
                    _tools.append(tool)
        return tool_docstrings

    def get_scratchpad(self):
        """Get the scratchpad from the workflow."""


OPERATION_PT = """
===== Operator =====
This section exists because LLMs need explicit task framing - it's not just about the operation name, but about setting the operational boundaries and execution mode. Like a function signature, it tells the LLM "you are now operating in this specific mode with these specific constraints."

===== Task =====
Without clear success criteria, LLMs can drift or hallucinate objectives. This section anchors the operation to concrete, measurable outcomes - it's the semantic equivalent of a unit test for the operation.
{task}

===== Context =====
LLMs lack persistent memory and operational state. This section provides the critical runtime context - what's happened before, what's the current state, and what's the operational environment. It's like providing the heap/stack state to a running program.
{context}

===== Knowledge =====
While LLMs have broad knowledge, they need domain-specific guardrails and patterns for consistent output. This section provides the "expert rules" that constrain and guide the LLM's decision-making process within the operation's domain.
{knowledge}

===== Actions =====
LLMs need explicit action spaces and valid transitions. This isn't just a list - it's a state machine definition showing valid transitions (-next->) between actions.
It prevents invalid action sequences and ensures operational coherence. However the sequences of the actions are recommended, not mandatory.
{action_rels}

===== Tools =====
Tools are the LLM's API to the external world. This section defines not just tool interfaces, but their operational semantics - how they transform state, what guarantees they provide, and how they can be composed safely.
{tool_docstrings}

===== Scratchpad =====
LLMs benefit from explicit reasoning chains. This workspace isn't just for show - it forces structured thinking and provides an audit trail for the operation's execution. It's debug output for LLM reasoning.
{scratchpad}

=====
"""
