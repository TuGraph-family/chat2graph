"""
Message view module for handling the transformation between internal message models
and API response formats.
"""

from typing import Any, Dict, List

from app.core.common.type import ChatMessageType
from app.core.model.job import Job
from app.core.model.job_graph import JobGraph
from app.core.model.message import AgentMessage, Message, TextMessage
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService


class MessageView:
    """Message view responsible for transforming internal message models to API response formats.

    This class ensures that internal field names (like chat_message_type) are
    properly converted to API field names (like message_type) for consistent API responses.
    """

    @staticmethod
    def serialize_message(message: Message) -> Dict[str, Any]:
        """Convert a TextMessage model to an API response dictionary.

        Changes chat_message_type (internal) to message_type (API) and
        payload (internal) to message (API).
        """
        if isinstance(message, AgentMessage):
            job_service: JobService = JobService.instance
            agent_service: AgentService = AgentService.instance
            sub_job_id: str = message.get_job_id()
            sub_job: Job = job_service.get_subjob(job_id=sub_job_id)
            original_job_ids = job_service.get_original_job_ids()

            for id in original_job_ids:
                job_graph: JobGraph = job_service.get_job_graph(job_id=id)
                if job_graph.has_vertex(sub_job_id):
                    expert_id: str = job_graph.get_expert_id(sub_job_id)
                    break
            assert expert_id, f"Expert ID not found for job ID {sub_job_id}"

            return {
                "id": message.get_id(),
                "job_id": sub_job_id,
                "job_goal": sub_job.goal,
                "assigned_expert_name": agent_service.leader.state.get_expert_by_id(expert_id),
                "agent_result": message.get_workflow_result_message().get_payload(),
                "timestamp": message.get_timestamp(),
                "message_type": ChatMessageType.TEXT.value,
                "role": "agent",
            }

        if isinstance(message, TextMessage):
            return {
                "id": message.get_id(),
                "session_id": message.get_session_id(),
                "message_type": message.get_chat_message_type().value,
                "job_id": message.get_job_id(),
                "role": message.get_role(),
                "message": message.get_payload(),  # Renamed from payload to message
                "timestamp": message.get_timestamp(),
                "assigned_expert_name": message.get_assigned_expert_name(),
                "others": message.get_others(),
            }
        raise ValueError(f"Unsupported message type: {type(message)}")

    @staticmethod
    def serialize_messages(messages: List[Message]) -> List[Dict[str, Any]]:
        """Serialize a list of text messages to a list of API response dictionaries"""
        return [MessageView.serialize_message(msg) for msg in messages]
