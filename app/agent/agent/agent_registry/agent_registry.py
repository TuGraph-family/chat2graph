from abc import ABC
from typing import Dict

from app.agent.profile import Profile


class AgentRegistry(ABC):
    """The registry of the agent."""

    def __init__(self):
        self.agent_profiles: Dict[str, Profile] = {}
