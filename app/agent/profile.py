from abc import ABC


class Profile(ABC):
    """The profile of the agent."""

    def __init__(self, profile_name: str, profile_description: str):
        self.name = profile_name
        self.description = profile_description
