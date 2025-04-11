from typing import Any, Dict, Tuple

from app.core.service.job_service import JobService
from app.server.manager.view.message_view import MessageViewTransformer


class JobManager:
    """Job Manager class to handle business logic for jobs"""

    def __init__(self):
        self._job_service: JobService = JobService.instance

    def get_conversation_view(self, job_id: str) -> Tuple[Dict[str, Any], str]:
        """Get message view (including thinking chain) for a specific job."""
        return MessageViewTransformer.serialize_conversation_view(
            self._job_service.get_conversation_view(original_job_id=job_id)
        ), "Message view retrieved successfully"
