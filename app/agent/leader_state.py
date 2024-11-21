from abc import ABC
from typing import Dict, List

import networkx as nx

from app.agent.agent import AgentConfig
from app.agent.expert import Expert
from app.agent.task import Task


class LeaderState(ABC):
    """Registry for managing expert agent initialization information.

    attributes:
        _expert_dict: the expert dictionary (expert_id -> expert_config).
        tasks: the oriented graph of the tasks.

        tasks schema
            {
                "task_id": {
                    "task": Task,
                }
            }
    """

    def __init__(self):
        # Store class and config information, not instances
        self._expert_dict: Dict[str, Expert] = {}  # expert_id -> expert_config
        self.tasks: nx.DiGraph = nx.DiGraph()

    def register(self, expert_id: str, expert: Expert) -> None:
        """Register information needed to initialize an expert agent."""

        if expert_id in self._expert_dict:
            raise ValueError(f"Expert {expert_id} already registered")

        # Store initialization information
        self._expert_dict[expert_id] = expert

    def create(self, expert_id: str, agent_config: AgentConfig) -> Expert:
        """Create a new instance of an expert agent."""
        if expert_id in self._expert_dict:
            raise ValueError(f"Expert with ID {expert_id} has been registered")
        expert = Expert(agent_config=agent_config)
        self.register(expert_id=expert_id, expert=expert)
        return expert

    def relese(self, expert_id: str) -> None:
        """Release the expert agent."""
        if expert_id in self._expert_dict:
            del self._expert_dict[expert_id]
        else:
            raise ValueError(f"Expert with ID {expert_id} not found")

    def list_experts(self) -> Dict[str, Expert]:
        """Return a dictionary of all registered expert information."""

        return dict(self._expert_dict)

    def add_task(
        self, task: Task, predecessors: List[Task], successors: List[Task]
    ) -> None:
        """Add a task to the task registry."""
        self.tasks.add_node(task.id, task=task)
        for predecessor in predecessors:
            self.tasks.add_edge(predecessor.id, task.id)
        for successor in successors:
            self.tasks.add_edge(task.id, successor.id)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from the task registry."""
        self.tasks.remove_node(task_id)

    def get_task(self, task_id: str) -> Task:
        """Get a task from the task registry."""
        return self.tasks.nodes[task_id]["task"]
