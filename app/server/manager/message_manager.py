from typing import Any, Dict, List, Tuple

from app.core.common.type import JobStatus
from app.core.model.message import TextMessage, WorkflowMessage
from app.core.sdk.agentic_service import AgenticService
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService


class MessageManager:
    """Message Manager class to handle business logic"""

    def __init__(self):
        self._agentic_service: AgenticService = AgenticService.instance or AgenticService.load()
        self._message_service: MessageService = MessageService.instance
        self._job_service: JobService = JobService.instance
        self._agent_service: AgentService = AgentService.instance

    def chat(
        self,
        session_id: str,
        payload: str,
        chat_message_type: str,
        others: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Create user message and system message return the response data.

        Args:
            session_id (str): ID of the associated session
            payload (str): Content of the message
            chat_message_type (str): Type of the message
            others (Optional[str], optional): Additional information. Defaults to None.

        Returns:
            Tuple[List[Dict[str, Any]], str]: A tuple containing a list of agent message details and
                success message
        """
        # create user message
        text_message = TextMessage(
            session_id=session_id,
            chat_message_type=chat_message_type,
            role="user",
            payload=payload,
            others=others,
        )
        self._message_service.create_text_message(text_message=text_message)

        # make the chat message to the mulit-agent system
        session_wrapper = self._agentic_service.session(session_id=session_id)
        # TODO: refactor the chat message to a more generic message
        job_wrapper = session_wrapper.submit(
            message=TextMessage(payload=payload, assigned_expert_name="Question Answering Expert")
        )

        # create system message
        system_chat_message = TextMessage(
            session_id=session_id,
            chat_message_type="chat",  # chat/text/graph/file/code
            job_id=job_wrapper.id,
            role="system",
            payload="",
            others=others,
        )
        self._message_service.create_text_message(system_chat_message)
        system_data = {
            "id": system_chat_message.get_id(),
            "session_id": system_chat_message.get_session_id(),
            "chat_message_type": system_chat_message.get_chat_message_type(),
            "job_id": system_chat_message.get_job_id(),
            "role": system_chat_message.get_role(),
            "message": system_chat_message.get_payload(),
            "timestamp": system_chat_message.get_timestamp(),
            "others": system_chat_message.get_others(),
        }
        return system_data, "Message created successfully"

    def get_agent_messages_by_job(self, original_job_id: str) -> Tuple[List[Dict[str, Any]], str]:
        """Get agent messages by job.

        Args:
            job (Job): The job instance

        Returns:
            Tuple[List[Dict[str, Any]], str]: A tuple containing a list of agent message details and
                success message
        """
        jobs = self._job_service.get_subjobs(original_job_id=original_job_id)
        data: List[Dict[str, Any]] = []
        for job in jobs:
            # get the agent messages
            agent_messages = self._message_service.get_agent_messages_by_job_id(job=job)

            # prepare the data
            data.extend(
                [
                    {
                        "id": msg.get_id(),
                        "job_id": msg.get_payload().id,
                        "job_goal": msg.get_payload().goal,
                        "assigned_expert_name": self._agent_service.leader.state.get_expert_by_id(
                            self._job_service.get_job_graph(job_id=job.id).get_expert_id(
                                msg.get_payload().id
                            )
                        )
                        .get_profile()
                        .name,
                        "agent_result": WorkflowMessage.serialize_payload(
                            msg.get_workflow_result_message().get_payload()
                        ),
                        "timestamp": msg.get_timestamp(),
                        "chat_message_type": "text",
                        "role": "agent",
                    }
                    for msg in agent_messages
                ]
            )
        return data, "Agent messages fetched successfully"

    def get_text_message(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Get message details by ID.

        If the job result is available, it will return the job result in the message details.

        Args:
            id (str): ID of the message

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing message details and success message
        """
        # get the chat message
        chat_message = self._message_service.get_text_message(id=id)

        # query the job result
        job_id = chat_message.get_job_id()
        assert job_id, "Job ID is not defined in the message"
        job_result = self._job_service.query_job_result(job_id=job_id)

        # check the job status
        if job_result.status == JobStatus.FAILED:
            print(f"Job failed for job_id: {job_id}")
            return {"status": job_result.status.value}, "Job failed"

        if job_result.status in [JobStatus.CREATED, JobStatus.RUNNING]:
            print(f"Job still in progress for job_id: {job_id}")
            return {"status": job_result.status.value}, "Job still in progress"

        # update the message with the job result
        new_message = self._message_service.update_text_message(
            id=id, payload=job_result.result.get_payload()
        )

        data = {
            "id": new_message.get_id(),
            "session_id": new_message.get_session_id(),
            "chat_message_type": new_message.get_chat_message_type(),
            "job_id": new_message.get_job_id(),
            "status": job_result.status.value,
            "role": new_message.get_role(),
            "message": new_message.get_payload(),
            "timestamp": new_message.get_timestamp(),
            "others": new_message.get_others(),
        }
        return data, "Message fetched successfully"

    def filter_text_messages_by_session(self, session_id: str) -> Tuple[List[Dict], str]:
        """Filter messages by session ID.

        Args:
            session_id (str): ID of the session

        Returns:
            Tuple[List[Dict], str]: A tuple containing a list of filtered message details and
                success message
        """
        chat_messages = self._message_service.filter_text_messages_by_session(session_id=session_id)
        message_list = [
            {
                "id": msg.get_id(),
                "session_id": msg.get_session_id(),
                "chat_message_type": msg.get_chat_message_type(),
                "job_id": msg.get_job_id(),
                "role": msg.get_role(),
                "message": msg.get_payload(),
                "timestamp": msg.get_timestamp(),
                "others": msg.get_others(),
            }
            for msg in chat_messages
        ]
        return message_list, f"Messages filtered by session ID {session_id} successfully"
