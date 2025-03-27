from typing import Any, Dict, List, Tuple, cast

from app.core.common.type import ChatMessageRole
from app.core.model.job_result import JobResult
from app.core.model.message import AgentMessage, MessageType
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.server.manager.view.message_view import MessageView, MessageViewTransformer


class JobManager:
    """Job Manager class to handle business logic for jobs"""

    def __init__(self):
        self._job_service: JobService = JobService.instance
        self._message_service: MessageService = MessageService.instance

    def get_conversation_view(self, job_id: str) -> Tuple[Dict[str, Any], str]:
        """Get message view (including thinking chain) for a specific job."""
        # get job details
        original_job = self._job_service.get_orignal_job(job_id)

        # get original job result
        orignial_job_result = self._job_service.query_job_result(job_id)

        # get the user question message
        question_message = self._message_service.get_text_message_by_job_id_and_role(
            job_id, ChatMessageRole.USER
        )

        # get the AI answer message
        answer_message = self._message_service.get_text_message_by_job_id_and_role(
            job_id, ChatMessageRole.SYSTEM
        )
        # get thinking chain messages
        message_result_pairs: List[Tuple[AgentMessage, JobResult]] = []  # to sort by timestamp

        subjob_ids = self._job_service.get_subjob_ids(original_job_id=original_job.id)
        for subjob_id in subjob_ids:
            # get the information, whose job is not legacy
            subjob = self._job_service.get_subjob(subjob_id=subjob_id)
            if not subjob.is_legacy:
                # get the subjob result
                subjob_result = self._job_service.get_job_result(job_id=subjob_id)

                # get the agent message
                agent_messages = cast(
                    List[AgentMessage],
                    self._message_service.get_message_by_job_id(
                        job_id=subjob_id, message_type=MessageType.AGENT_MESSAGE
                    ),
                )
                if len(agent_messages) == 1:
                    thinking_message = agent_messages[0]
                elif len(agent_messages) == 0:
                    # handle the unexecuted subjob
                    thinking_message = AgentMessage(
                        job_id=subjob_id, payload="The subjob is not executed"
                    )
                else:
                    raise ValueError(
                        f"Multiple agent messages found for job ID {subjob_id}: {agent_messages}"
                    )
                # store the pair of message and result
                message_result_pairs.append((thinking_message, subjob_result))

        # sort pairs by message timestamp
        message_result_pairs.sort(
            key=lambda pair: cast(int, pair[0].get_timestamp())
            if pair[0].get_timestamp() is not None
            else float("inf")
        )

        # separate the sorted pairs back into individual lists
        thinking_messages: List[AgentMessage] = [pair[0] for pair in message_result_pairs]
        subjob_results: List[JobResult] = [pair[1] for pair in message_result_pairs]

        return MessageViewTransformer.serialize_conversation_view(
            MessageView(
                question=question_message,
                answer=answer_message,
                answer_metrics=orignial_job_result,
                thinking_messages=thinking_messages,
                thinking_metrics=subjob_results,
            )
        ), "Message view retrieved successfully"
