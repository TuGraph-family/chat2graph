from typing import List

from app.env.consensus.consensus import Consensus


class ConsensusServer:
    """Consensus Manager manages the consensus of the multi-agent system."""

    def __init__(self, consensus: List[Consensus] = None):
        self.consensuses: List[Consensus] = consensus or []

    def get_consensuses_text(self) -> str:
        """Get the consensuses text."""
        return str(consensus.content + "\n\n" for consensus in self.consensuses)
