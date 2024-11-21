from app.env.consensus.consensus_manager import ConsensusServer
from app.env.insight.insight_server import TextInsightServer


class Env:
    """Environment Manager manages the environment of the multi-agent system."""

    def __init__(self):
        self.consensus_server = ConsensusServer()
        self.text_insight_server = TextInsightServer()
        self.image_insight_server = None
        self.table_insight_server = None

    async def recommend_info(self, data: str) -> str:
        """Recommend information."""
