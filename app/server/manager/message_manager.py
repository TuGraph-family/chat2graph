from typing import Any, Dict, List, Optional, Tuple

from app.core.common.type import JobStatus
from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.server.common.util import ServiceException


class MessageManager:
    """Message Manager class to handle business logic"""

    def __init__(self):
        self._agentic_service: AgenticService = AgenticService.load()
        self._message_service: MessageService = MessageService.instance
        self._job_service: JobService = JobService.instance

    def chat(
        self,
        session_id: str,
        message: str,
        message_type: str,
        others: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Create user message and system message return the response data.

        Args:
            session_id (str): ID of the associated session
            message (str): Content of the message
            message_type (str): Type of the message
            others (Optional[str], optional): Additional information. Defaults to None.

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing message details and success message.
        """
        try:
            # create user message
            self._message_service.create_message(
                session_id=session_id,
                message_type=message_type,
                role="user",
                message=message,
                others=others,
            )

            # make the chat message to the mulit-agent system
            session_wrapper = self._agentic_service.session(session_id=session_id)
            # TODO: refactor the chat message to a more generic message
            job_wrapper = session_wrapper.submit(
                message=TextMessage(
                    payload=message, assigned_expert_name="Question Answering Expert"
                )
            )

            # create system message
            system_chat_message = self._message_service.create_message(
                session_id=session_id,
                message_type="chat",
                job_id=job_wrapper.id,
                role="system",
                message="",
                others=others,
            )
            system_data = {
                "id": system_chat_message.get_id(),
                "session_id": system_chat_message.get_session_id(),
                "message_type": system_chat_message.get_message_type(),
                "job_id": system_chat_message.get_job_id(),
                "role": system_chat_message.get_role(),
                "message": system_chat_message.get_payload(),
                "timestamp": system_chat_message.get_timestamp(),
                "others": system_chat_message.get_others(),
            }
            return system_data, "Message created successfully"
        except Exception as e:
            raise ServiceException(f"Failed to create message: {str(e)}") from e

    def get_message(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Get message details by ID.

        Args:
            id (str): ID of the message

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing message details and success message
        """
        try:
            # get the chat message
            chat_message = self._message_service.get_message(id=id)

            # query the job result
            job_id = chat_message.get_job_id()
            job_result = self._job_service.query_job_result(job_id=job_id)

            # check the job status
            if job_result.status == JobStatus.FAILED:
                print(f"Job failed for job_id: {job_id}")
                return {"status": job_result.status.value}, "Job failed"

            if job_result.status in [JobStatus.CREATED, JobStatus.RUNNING]:
                print(f"Job still in progress for job_id: {job_id}")
                return {"status": job_result.status.value}, "Job still in progress"

            # update the message with the job result
            new_message = self._message_service.update_message(
                id=id, message=job_result.result.get_payload()
            )

            data = {
                "id": new_message.get_id(),
                "session_id": new_message.get_session_id(),
                "message_type": new_message.get_message_type(),
                "job_id": new_message.get_job_id(),
                "status": job_result.status.value,
                "role": new_message.get_role(),
                "message": new_message.get_payload(),
                "timestamp": new_message.get_timestamp(),
                "others": new_message.get_others(),
            }
            return data, "Message fetched successfully"
        except Exception as e:
            raise ServiceException(f"Failed to fetch message: {str(e)}") from e

    def filter_messages_by_session(self, session_id: str) -> Tuple[List[Dict], str]:
        """Filter messages by session ID.

        Args:
            session_id (str): ID of the session

        Returns:
            Tuple[List[Dict], str]: A tuple containing a list of filtered message details and
                success message
        """
        try:
            chat_messages = self._message_service.filter_messages_by_session(session_id=session_id)
            message_list = [
                {
                    "id": msg.get_id(),
                    "session_id": msg.get_session_id(),
                    "message_type": msg.get_message_type(),
                    "job_id": msg.get_job_id(),
                    "role": msg.get_role(),
                    "message": msg.get_payload(),
                    "timestamp": msg.get_timestamp(),
                    "others": msg.get_others(),
                }
                for msg in chat_messages
            ]
            return message_list, f"Messages filtered by session ID {session_id} successfully"
        except Exception as e:
            raise ServiceException(f"Failed to filter messages by session: {str(e)}") from e
