from typing import Any, Dict, List, Tuple, cast

from app.core.common.type import JobStatus
from app.core.model.job_result import JobResult
from app.core.model.message import AgentMessage, MessageType
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.server.manager.view.job_view import JobView
from app.server.manager.view.message_view import MessageView


class JobManager:
    """Job Manager class to handle business logic for jobs"""

    def __init__(self):
        self._job_service: JobService = JobService.instance
        self._message_service: MessageService = MessageService.instance

    def get_message_view(self, job_id: str) -> Tuple[Dict[str, Any], str]:
        """Get message view (including thinking chain) for a specific job."""
        # get job details
        original_job = self._job_service.get_orignal_job(job_id)
        subjob_ids = self._job_service.get_subjob_ids(original_job_id=original_job.id)

        # get the user question message
        question_message = self._message_service.get_text_message_by_job_and_role(
            original_job, "USER"
        )

        # get the AI answer message
        answer_message = self._message_service.get_text_message_by_job_and_role(
            original_job, "SYSTEM"
        )

        # get original job result
        orignial_job_result = self._job_service.query_job_result(job_id)

        # get thinking chain messages
        thinking_messages: List[AgentMessage] = []
        subjob_results: List[JobResult] = []
        for subjob_id in subjob_ids:
            subjob_result = self._job_service.get_job_result(job_id=subjob_id)
            subjob_results.append(subjob_result)

            if subjob_result.status == JobStatus.FINISHED:
                agent_messages = cast(
                    List[AgentMessage],
                    self._message_service.get_message_by_job_id(
                        job_id=subjob_id, type=MessageType.AGENT_MESSAGE
                    ),
                )
                assert len(agent_messages) == 1, (
                    f"Subjob {subjob_id} has multiple or no agent messages."
                )
                thinking_messages.append(agent_messages[0])
            else:
                # handle unfinished subjobs, and the agent message is saved in the db
                thinking_message = AgentMessage(
                    id=subjob_id,
                    job_id=subjob_id,
                    payload="",
                    workflow_messages=[],
                    timestamp=0,
                )
                thinking_messages.append(thinking_message)

        # format response according to the requirements
        # TODO: rerange the view by the timestamp
        message_view_data = {
            "question": {"message": MessageView.serialize_message(question_message)},
            "answer": {
                "message": MessageView.serialize_message(answer_message),
                "metrics": JobView.serialize_job_result(orignial_job_result),
                "thinking": [
                    {
                        "message": MessageView.serialize_message(thinking_message),
                        "metrics": JobView.serialize_job_result(subjob_result),
                    }
                    for thinking_message, subjob_result in zip(
                        thinking_messages, subjob_results, strict=True
                    )
                ],
            },
        }

        return message_view_data, "Message view retrieved successfully"
