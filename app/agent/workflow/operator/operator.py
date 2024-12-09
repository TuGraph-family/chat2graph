from typing import Dict, List, Optional, Set
from uuid import uuid4

import networkx as nx  # type: ignore

from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.reasoner import ReasonerCaller
from app.agent.task import Task
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit, ToolkitGraphType


class Operator(ReasonerCaller):
    """Operator is a sequence of actions and tools that need to be executed.

    Attributes:
        _id (str): The unique identifier of the operator.
        _reasoner (DualModelReasoner): The dual model reasoner.
        _operator_prompt_template (str): The prompt template of the operator.
        _toolkit (Toolkit): The toolkit that contains the actions and tools.
        _actions (List[Action]): The actions that need to be executed.
        _recommanded_actions (List[Action]): The recommanded actions from the toolkit.
        _embedding_vector (List[float]): The embedding vector of the operator.
    """

    def __init__(
        self,
        operator_prompt_template: str,
        toolkit: Toolkit,
        actions: List[Action],
        id: str = str(uuid4()),
    ):
        super().__init__(id=id)

        self._operator_prompt_template: str = operator_prompt_template
        self._toolkit: Toolkit = toolkit
        self._actions: List[Action] = actions
        self._recommanded_actions: Optional[List[Action]] = None

        # TODO: embedding vector of context
        self._embedding_vector: Optional[List[float]] = None

    async def initialize(self, threshold: float = 0.5, hops: int = 0):
        """Initialize the operator."""
        self._recommanded_actions = await self.get_recommanded_actions(
            threshold=threshold, hops=hops
        )

    async def execute(
        self,
        reasoner: DualModelReasoner,
        task: Task,  # TODO: will change the name in the next PR
        scratchpad: str,  # TODO: need to be removed
    ) -> Dict[str, str]:
        """Execute the operator by LLM client."""
        operator_prompt = await self.format_operation_prompt(
            task=self._task,
            context=context,
            scratchpad=scratchpad,
        )
        print(f"Operator prompt:\n{operator_prompt}")

        result = await reasoner.infer(
            caller=self,
            reasoning_rounds=reasoning_rounds,
            print_messages=print_messages,
        )
        return {"scratchpad": result}

    def verify_actions(self, actions: List[Action]) -> bool:
        """Verify the actions."""
        return self._toolkit.verify_actions(actions)

    async def get_knowledge(self) -> str:
        """Get the knowledge from the knowledge base."""
        # TODO: get the knowledge from the knowledge base
        return ""

    async def get_recommanded_actions(
        self, threshold: float = 0.5, hops: int = 0
    ) -> List[Action]:
        """Get the actions from the toolkit."""
        toolkit_subgraph: nx.DiGraph = await self._toolkit.recommend_tools(
            actions=self._actions, threshold=threshold, hops=hops
        )
        recommanded_actions: List[Action] = []
        for node in toolkit_subgraph.nodes:
            if toolkit_subgraph.nodes[node]["type"] == ToolkitGraphType.ACTION:
                action: Action = toolkit_subgraph.nodes[node]["data"]
                next_action_ids = [
                    toolkit_subgraph.nodes[n]["data"].id
                    for n in toolkit_subgraph.successors(node)
                    if toolkit_subgraph.nodes[n]["type"] == ToolkitGraphType.ACTION
                ]
                tools = [
                    toolkit_subgraph.nodes[n]["data"]
                    for n in toolkit_subgraph.successors(node)
                    if toolkit_subgraph.nodes[n]["type"] == ToolkitGraphType.TOOL
                ]
                recommanded_actions.append(
                    Action(
                        id=action.id,
                        name=action.name,
                        description=action.description,
                        next_action_ids=next_action_ids,
                        tools=tools,
                    )
                )

        return recommanded_actions

    def get_action_rels(self) -> str:
        """Get the action relationships from the toolkit."""
        if self._recommanded_actions is None:
            raise ValueError("The recommanded actions have not been initialized.")

        action_rels = ""
        for action in self._recommanded_actions:
            next_action_names = [
                self._toolkit.get_action(a_id).name for a_id in action.next_action_ids
            ]
            action_rels += (
                f"[{action.name}: {action.description}] -next-> "
                f"{str(next_action_names)}\n"
            )

        return action_rels

    def get_tools_from_actions(self) -> List[Tool]:
        """Get the tools from the actions."""
        if self._recommanded_actions is None:
            raise ValueError("The recommanded actions have not been initialized.")
        seen_ids: Set[str] = set()
        tools = []
        for action in self._recommanded_actions:
            assert action.tools is not None
            for tool in action.tools:
                if tool.id not in seen_ids:
                    seen_ids.add(tool.id)
                    tools.append(tool)
        return tools

    def get_tool_docstrings(self) -> str:
        """Get the tool names and docstrings from the toolkit."""
        tools = self.get_tools_from_actions()
        tool_docstrings = ""
        for tool in tools:
            tool_docstrings += (
                f"func {tool.function.__name__}:\n{tool.function.__doc__}\n"
            )
        return tool_docstrings

    async def format_operation_prompt(
        self, task: str, context: str, scratchpad: str
    ) -> str:
        """Format the operation prompt."""
        return OPERATION_PT.format(
            task=task,
            context=context,
            knowledge=await self.get_knowledge(),
            action_rels=self.get_action_rels(),
            tool_docstrings=self.get_tool_docstrings(),
            scratchpad=scratchpad,
        )

    def get_id(self) -> str:
        """Get the id."""
        return self._id


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
