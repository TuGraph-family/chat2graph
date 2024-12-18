from typing import List, Optional, Set

import networkx as nx  # type: ignore

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.env.insight.insight import Insight, TextInsight
from app.knowledge_base.knowlege_base_factory import KnowledgeService
from app.memory.message import WorkflowMessage
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit, ToolkitGraphType, ToolkitService


class Operator:
    """Operator is a sequence of actions and tools that need to be executed.

    Attributes:
        _id (str): The unique identifier of the operator.
        _config (OperatorConfig): The configuration of the operator.
        _toolkit_service (ToolkitService): The toolkit service.
        _knowledge_service (Optional[KnowledgeService]): The knowledge service.
        _environment_service (Optional[KnowledgeService]): The environment service.
    """

    def __init__(
        self,
        config: OperatorConfig,
        toolkit_service: ToolkitService = ToolkitService(Toolkit()),
        knowledge_service: Optional[KnowledgeService] = None,
        environment_service: Optional[KnowledgeService] = None,
    ):
        self._config: OperatorConfig = config
        # TODO: need to start the service firstly
        self._toolkit_service: ToolkitService = toolkit_service
        self._knowledge_service: Optional[KnowledgeService] = knowledge_service
        self._environment_service: Optional[KnowledgeService] = environment_service

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
    ) -> WorkflowMessage:
        """Execute the operator by LLM client."""
        tools = await self.get_tools_from_actions()

        task = Task(
            job=job,
            operator_config=self._config,
            workflow_messages=workflow_messages,
            tools=tools,
            action_rels=await self.get_action_rels(),
            knowledge=await self.get_knowledge(),
            insights=await self.get_env_insights(),
        )

        result = await reasoner.infer(task=task)

        return WorkflowMessage(content={"scratchpad": result})

    async def get_knowledge(self) -> str:
        """Get the knowledge from the knowledge base."""
        # TODO: get the knowledge from the knowledge base
        return "Do not have provieded any knowledge yet."

    async def get_env_insights(self) -> List[Insight]:
        """Get the environment information."""
        # TODO: get the environment information
        return [
            TextInsight(
                tags=[],
                entities=[],
                content="Do not have provieded any environment information yet.",
            )
        ]

    async def get_rec_actions(self) -> List[Action]:
        """Get the recommanded actions from the toolkit."""

        # get the subgraph from the toolkit based on the provided actions, threshold, and hops
        toolkit_subgraph: nx.DiGraph = (
            await self._toolkit_service.get_toolkit().recommend_tools(
                actions=self._config.actions,
                threshold=self._config.threshold,
                hops=self._config.hops,
            )
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
        action_rels = ""
        rec_actions = await self.get_rec_actions()

        for action in rec_actions:
            next_action_names = [
                self._toolkit_service.get_toolkit().get_action(a_id).name
                for a_id in action.next_action_ids
            ]
            action_rels += (
                f"[{action.name}: {action.description}] -next-> "
                f"{str(next_action_names)}\n"
            )

        return action_rels

    async def get_tools_from_actions(self) -> List[Tool]:
        """Get the tools from the recommanded actions."""
        seen_ids: Set[str] = set()
        tools: List[Tool] = []
        rec_actions = await self.get_rec_actions()

        for action in rec_actions:
            assert action.tools is not None
            for tool in action.tools:
                if tool.id not in seen_ids:
                    seen_ids.add(tool.id)
                    tools.append(tool)
        return tools
