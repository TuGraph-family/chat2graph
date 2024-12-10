from dataclasses import dataclass
from typing import List, Optional, Set, Tuple, Type

import networkx as nx  # type: ignore

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner, ReasonerCaller
from app.agent.reasoner.task import Task, TaskDescriptor
from app.agent.workflow.operator.frame import Frame
from app.commom.prompt import OPERATION_CONTEXT_PROMPT_TEMPLATE
from app.knowledge_base.knowlege_base_factory import (
    KnowledgeBaseProvider,
    KnowledgeBaseRegistry,
)
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit, ToolkitGraphType


@dataclass
class OperatorConfig:
    """Operator configuration."""

    instruction: str
    toolkit: Toolkit
    actions: List[Action]
    threshold: float = 0.5
    hops: int = 0
    operator_context_prompt_template: str = OPERATION_CONTEXT_PROMPT_TEMPLATE
    profile: str = ""
    output_schema: str = ""
    knowledge_base_registry: Type[KnowledgeBaseRegistry] = KnowledgeBaseRegistry
    environment_provider: Optional[KnowledgeBaseProvider] = None


class Operator(ReasonerCaller):
    """Operator is a sequence of actions and tools that need to be executed.

    Attributes:
        _id (str): The unique identifier of the operator.
        _profile (str): The profile of the operator.
        _instruction (str): The instruction of the operator.
        _output_schema (str): The output schema of the operator.
        _operator_context_prompt_template (str): The prompt template of the operator.
        _toolkit (Toolkit): The toolkit that contains the actions and tools.
        _actions (List[Action]): The actions that need to be executed.
        _rec_actions (List[Action]): The recommanded actions from the toolkit.
        _embedding_vector (List[float]): The embedding vector of the operator.
        _knowledge_base_registry (Type[KnowledgeBaseRegistry]): The knowledge base registry.
        _environment_provider (Optional[KnowledgeBaseProvider]): The environment provider.
    """

    def __init__(self, config: OperatorConfig, id: Optional[str] = None):
        super().__init__(id=id)

        self._profile: str = config.profile
        self._instruction: str = config.instruction
        self._output_schema: str = config.output_schema
        self._operator_context_prompt_template = config.operator_context_prompt_template

        self._toolkit: Toolkit = config.toolkit
        self._actions: List[Action] = config.actions
        self._rec_actions: List[Action] = []

        self._knowledge_base_registry: Type[KnowledgeBaseRegistry] = (
            config.knowledge_base_registry
        )
        # TODO: the type of the _environment_provider is under discussions
        self._environment_provider: Optional[KnowledgeBaseProvider] = (
            config.environment_provider
        )  # viewing the env as a knowledge base

        self._threshold: float = config.threshold
        self._hops: int = config.hops

        # TODO: Embedding vector of operator's ablitity
        self._embedding_vector: Optional[List[float]] = None

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        frames: Optional[List[Frame]] = None,
    ) -> Frame:
        """Execute the operator by LLM client."""
        task, tools = await self._prepare_infer_para(frames=frames, job=job)

        result = await reasoner.infer(task=task, tools=tools, caller=self)
        return Frame(scratchpad=result)

    async def get_knowledge(self) -> str:
        """Get the knowledge from the knowledge base."""
        # TODO: get the knowledge from the knowledge base
        return "Do not have provieded any knowledge yet."

    async def get_env_info(self) -> str:
        """Get the environment information."""
        # TODO: get the environment information
        return "Do not have provieded any environment information yet."

    async def init_rec_actions(self):
        """Initialize the operator."""
        self._rec_actions = await self.get_rec_actions()

    async def get_rec_actions(self) -> List[Action]:
        """Get the recommanded actions from the toolkit."""

        # get the subgraph from the toolkit based on the provided actions, threshold, and hops
        toolkit_subgraph: nx.DiGraph = await self._toolkit.recommend_tools(
            actions=self._actions, threshold=self._threshold, hops=self._hops
        )

        # get the recommanded actions from the subgraph
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

    async def get_action_rels(self) -> str:
        """Format the action relationships from the recommanded actions."""
        # TOOD: can the operator does not have any recommanded actions?
        if len(self._rec_actions) == 0:
            await self.init_rec_actions()

        action_rels = ""
        for action in self._rec_actions:
            next_action_names = [
                self._toolkit.get_action(a_id).name for a_id in action.next_action_ids
            ]
            action_rels += (
                f"[{action.name}: {action.description}] -next-> "
                f"{str(next_action_names)}\n"
            )

        return action_rels

    async def get_tools_from_actions(self) -> List[Tool]:
        """Get the tools from the recommanded actions."""
        # TOOD: can the operator does not have any recommanded actions?
        if len(self._rec_actions) == 0:
            await self.init_rec_actions()

        seen_ids: Set[str] = set()
        tools: List[Tool] = []
        for action in self._rec_actions:
            assert action.tools is not None
            for tool in action.tools:
                if tool.id not in seen_ids:
                    seen_ids.add(tool.id)
                    tools.append(tool)
        return tools

    async def _prepare_infer_para(
        self, job: Job, frames: Optional[List[Frame]] = None
    ) -> Tuple[Task, List[Tool]]:
        """Prepare the parameters for the operator calling the reasoner to infer."""
        task_descriptor = TaskDescriptor()

        tools = await self.get_tools_from_actions()

        if frames is None:
            workload_content = ""
        else:
            workload_content = "\n".join([frame.scratchpad for frame in frames])

        task = task_descriptor.aggregate(
            profile=self._profile,
            instruction=self._instruction,
            output_schema=self._output_schema,
            knowledge=await self.get_knowledge(),
            env_info=await self.get_env_info(),
            action_rels=await self.get_action_rels(),
            scratchpad=workload_content,
            job=job,
            operator_context_prompt_template=self._operator_context_prompt_template,
        )
        return task, tools

    def get_id(self) -> str:
        """Get the id."""
        return self._id
