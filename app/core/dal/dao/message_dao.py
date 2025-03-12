from typing import Any, Dict, List, Optional, cast

from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.message_do import (
    AgentMessageDo,
    MessageDo,
    ModelMessageAO,
    TextMessageDo,
    WorkflowMessageDo,
)
from app.core.model.job import Job
from app.core.model.message import (
    AgentMessage,
    Message,
    MessageType,
    ModelMessage,
    TextMessage,
    WorkflowMessage,
)


class MessageDao(Dao[MessageDo]):
    """Message dao"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(MessageDo, session)

    def save_message_do(self, message: Message) -> MessageDo:
        """Create a new message."""
        try:
            message_model = self.__save_message_do(message)
            self.session.add(message_model)
            self.session.commit()
            return message_model
        except Exception as e:
            self.session.rollback()
            raise e

    def __save_message_do(self, message: Message) -> MessageDo:
        """Create a message model instance."""

        if isinstance(message, WorkflowMessage):
            return WorkflowMessageDo(
                type=MessageType.WORKFLOW_MESSAGE.value,
                payload=WorkflowMessage.serialize_payload(message.get_payload()),
                job_id=message.get_id(),
                id=message.get_id(),
                timestamp=message.get_timestamp(),
            )

        if isinstance(message, AgentMessage):
            related_message_ids: List[str] = [wf.get_id() for wf in message.get_workflow_messages()]
            return AgentMessageDo(
                type=MessageType.AGENT_MESSAGE.value,
                job_id=message.get_job_id(),
                lesson=message.get_lesson(),
                related_message_ids=related_message_ids,
                timestamp=message.get_timestamp(),
                id=message.get_id(),
            )

        if isinstance(message, ModelMessage):
            # TODO: to refine the fields for model message
            # source_type: MessageSourceType = MessageSourceType.MODEL, # TODO
            # function_calls: Optional[List[FunctionCallResult]] = None,# TODO

            return ModelMessageAO(
                type=MessageType.MODEL_MESSAGE.value,
                payload=message.get_payload(),
                timestamp=message.get_timestamp(),
                id=message.get_id(),
                job_id=message.get_job_id(),
                step=message.get_step(),
            )

        if isinstance(message, TextMessage):
            return TextMessageDo(
                type=MessageType.TEXT_MESSAGE.value,
                id=message.get_id(),
                payload=message.get_payload(),
                timestamp=message.get_timestamp(),
                session_id=message.get_session_id(),
                job_id=message.get_job_id(),
                role=message.get_role(),
                assigned_expert_name=message.get_assigned_expert_name(),
                others=message.get_others(),
            )
        raise ValueError(f"Unsupported message type: {type(message)}")

    def get_by_type(self, type: MessageType) -> List[MessageDo]:
        """get messages by type"""
        return self.session.query(self._model).filter(self._model.type == type.value).all()

    def get_workflow_message(self, id: str) -> WorkflowMessage:
        """Get a message by ID."""
        # fetch the message
        result = self.get_by_id(id=id)
        if not result:
            raise ValueError(f"Workflow message with ID {id} not found")
        payload: Dict[str, Any] = WorkflowMessage.deserialize_payload(str(result.payload))
        return WorkflowMessage(
            id=str(result.id),
            payload=payload,
            job_id=str(result.job_id),
            timestamp=int(result.timestamp),
        )

    def get_workflow_message_payload(self, workflow_message_id: str) -> Optional[Dict[str, Any]]:
        """get message payload"""
        message = self.get_by_id(workflow_message_id)
        if message and message.payload:
            return WorkflowMessage.deserialize_payload(str(message.payload))
        raise ValueError(f"Workflow message {workflow_message_id} not found")

    def get_agent_messages_by_job(self, job: Job) -> List[AgentMessage]:
        """Get agent messages by job ID."""
        # fetch agent messages
        results: List[AgentMessageDo] = (
            self.session.query(self._model)
            .filter(
                self._model.type == MessageType.AGENT_MESSAGE.value,
                self._model.job_id == job.id,
            )
            .all()
        )

        if len(results) > 1:
            print(f"[Warning] The job {id} is executed multiple times.")

        agent_messages: List[AgentMessage] = [
            AgentMessage(
                id=str(result.id),
                job_id=job.id,
                workflow_messages=[
                    self.get_workflow_message(wf_id)
                    for wf_id in list(result.related_message_ids or [])
                ],
                timestamp=int(result.timestamp),
            )
            for result in results
        ]

        return agent_messages

    def get_agent_related_message_ids(self, id: str) -> List[str]:
        """get linked workflow ids"""
        message = self.get_by_id(id)
        if message and message.related_message_ids:
            return cast(List[str], message.related_message_ids)
        return []

    def get_agent_workflow_messages(self, id: str) -> List[WorkflowMessageDo]:
        """get all workflow messages linked to this agent message"""
        workflow_ids = self.get_agent_related_message_ids(id)
        if workflow_ids:
            return (
                self.session.query(WorkflowMessageDo)
                .filter(WorkflowMessageDo.id.in_(workflow_ids))
                .all()
            )
        return []

    def get_agent_workflow_result_message(self, id: str) -> Optional[WorkflowMessageDo]:
        """get the workflow result message (assumes only one exists)"""
        workflow_messages = self.get_agent_workflow_messages(id)
        if len(workflow_messages) != 1:
            raise ValueError("The agent message received no or multiple workflow result messages.")
        return workflow_messages[0] if workflow_messages else None
