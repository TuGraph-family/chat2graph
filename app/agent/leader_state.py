from abc import ABC
from typing import Dict, List

import networkx as nx

from app.agent.agent import AgentConfig
from app.agent.expert import Expert
from app.agent.task import Task


class LeaderState(ABC):
    """Leader State is uesd to manage expert agent and tasks.

    attributes:
        _tasks: the oriented graph of the tasks.
        _expert_assignments: the expert dictionary (task_id -> expert).

        tasks schema
            {
                "task_id": {
                    "task": Task,
                }
            }
    """

    def __init__(self):
        # Store class and config information, not instances
        self._tasks: nx.DiGraph = nx.DiGraph()
        self._expert_assignments: Dict[str, Expert] = {}  # task_id -> expert

    def register(self, task_id: str, expert: Expert) -> None:
        """Register information needed to assign a task to an expert."""

        if task_id in self._expert_assignments:
            raise ValueError(f"Task with ID {task_id} already registered")

        # Store initialization information
        self._expert_assignments[task_id] = expert

    def create(self, task_id: str, agent_config: AgentConfig) -> Expert:
        """Create a new instance of an expert agent."""
        if task_id in self._expert_assignments:
            raise ValueError(f"Task with ID {task_id} has been registered")
        expert = Expert(agent_config=agent_config)
        self.register(task_id=task_id, expert=expert)
        return expert

    def release(self, task_id: str) -> None:
        """Release the expert agent."""
        if task_id in self._expert_assignments:
            del self._expert_assignments[task_id]
        raise ValueError(f"Task with ID {task_id} not found in the registry")

    def list_expert_assignmentss(self) -> Dict[str, Expert]:
        """Return a dictionary of all registered expert information."""

        return dict(self._expert_assignments)

    def add_task(self, task: Task, predecessors: List[Task], successors: List[Task]) -> None:
        """Add a task to the task registry."""
        self._tasks.add_node(task.id, task=task)
        for predecessor in predecessors:
            self._tasks.add_edge(predecessor.id, task.id)
        for successor in successors:
            self._tasks.add_edge(task.id, successor.id)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from the task registry."""
        self._tasks.remove_node(task_id)

    def get_task(self, task_id: str) -> Task:
        """Get a task from the task registry."""
        return self._tasks.nodes[task_id]["task"]
