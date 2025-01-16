from typing import List, Optional

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.env.insight.insight import Insight
from app.knowledge.knowlege_service import KnowledgeService
from app.memory.message import WorkflowMessage
from app.toolkit.toolkit import Toolkit, ToolkitService


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
        task = await self._build_task(job, workflow_messages)

        result = await reasoner.infer(task=task)

        return WorkflowMessage(content={"scratchpad": result})

    async def _build_task(self, job, workflow_messages):
        (
            rec_tools,
            rec_actions,
        ) = await self._toolkit_service.get_toolkit().recommend_tools(
            actions=self._config.actions,
            threshold=self._config.threshold,
            hops=self._config.hops,
        )
        task = Task(
            job=job,
            operator_config=self._config,
            workflow_messages=workflow_messages,
            tools=rec_tools,
            actions=rec_actions,
            knowledge=await self.get_knowledge(),
            insights=await self.get_env_insights(),
        )
        return task

    async def get_knowledge(self) -> str:
        """Get the knowledge from the knowledge base."""
        # TODO: get the knowledge from the knowledge base
        return "Do not have provieded any knowledge yet."

    async def get_env_insights(self) -> Optional[List[Insight]]:
        """Get the environment information."""
        # TODO: get the environment information
        return None

    def get_id(self) -> str:
        """Get the operator id."""
        return self._config.id
