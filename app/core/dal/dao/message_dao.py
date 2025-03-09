from typing import Any, Dict, List, Optional, cast

from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import DAO
from app.core.dal.model.message_model import (
    AgentMessageModel,
    MessageModel,
    MessageType,
    ModelMessageModel,
    TextMessageModel,
    WorkflowMessageModel,
)
from app.core.model.job import Job
from app.core.model.message import AgentMessage, Message, ModelMessage, TextMessage, WorkflowMessage


class MessageModelFactory:
    """Factory class to create message model instances."""

    @staticmethod
    def create_message_model(message: Message, **kwargs: Any) -> MessageModel:
        """Create a message model instance."""

        if isinstance(message, WorkflowMessage):
            assert "job_id" in kwargs and isinstance(kwargs["job_id"], str), (
                "job_id is required, and must be a string"
            )
            return WorkflowMessageModel(
                type=MessageType.WORKFLOW_MESSAGE.value,
                payload=WorkflowMessage.serialize_payload(message.get_payload()),
                job_id=kwargs["job_id"],
                id=message.get_id(),
                timestamp=message.get_timestamp(),
            )

        if isinstance(message, AgentMessage):
            linked_workflow_ids: List[str] = [wf.get_id() for wf in message.get_workflow_messages()]
            return AgentMessageModel(
                type=MessageType.AGENT_MESSAGE.value,
                job_id=message.get_payload().id,
                lesson=message.get_lesson(),
                linked_workflow_ids=linked_workflow_ids,
                timestamp=message.get_timestamp(),
                id=message.get_id(),
            )

        if isinstance(message, ModelMessage):
            # TODO: to refine the fields for model message
            # source_type: MessageSourceType = MessageSourceType.MODEL, # TODO
            # function_calls: Optional[List[FunctionCallResult]] = None,# TODO

            assert "job_id" in kwargs and isinstance(kwargs["job_id"], str), (
                "job_id is required, and must be a string"
            )
            assert "step" in kwargs and isinstance(kwargs["step"], str), (
                "step is required, and must be a string"
            )
            return ModelMessageModel(
                type=MessageType.MODEL_MESSAGE.value,
                payload=message.get_payload(),
                timestamp=message.get_timestamp(),
                id=message.get_id(),
                job_id=kwargs["job_id"],
                step=kwargs["step"],
            )

        if isinstance(message, TextMessage):
            return TextMessageModel(
                type=MessageType.TEXT_MESSAGE.value,
                id=message.get_id(),
                payload=message.get_payload(),
                timestamp=message.get_timestamp(),
                session_id=message.get_session_id(),
                chat_message_type=message.get_chat_message_type(),
                job_id=message.get_job_id(),
                role=message.get_role(),
                assigned_expert_name=message.get_assigned_expert_name(),
                others=message.get_others(),
            )
        raise ValueError(f"Unsupported message type: {type(message)}")


class MessageDAO(DAO[MessageModel]):
    """Message dao"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(MessageModel, session)

    def create_message(self, message: Message, **kwargs) -> MessageModel:
        """Create a new message."""
        try:
            message_model = MessageModelFactory.create_message_model(message, **kwargs)
            self.session.add(message_model)
            self.session.commit()
            return message_model
        except Exception as e:
            self.session.rollback()
            raise e

    def get_by_type(self, type: MessageType) -> List[MessageModel]:
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
            timestamp=str(result.timestamp),
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
        results: List[AgentMessageModel] = (
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
                job=job,
                workflow_messages=[
                    self.get_workflow_message(wf_id)
                    for wf_id in list(result.linked_workflow_ids or [])
                ],
                timestamp=str(result.timestamp),
            )
            for result in results
        ]

        return agent_messages

    def get_agent_linked_workflow_ids(self, id: str) -> List[str]:
        """get linked workflow ids"""
        message = self.get_by_id(id)
        if message and message.linked_workflow_ids:
            return cast(List[str], message.linked_workflow_ids)
        return []

    def get_agent_workflow_messages(self, id: str) -> List[WorkflowMessageModel]:
        """get all workflow messages linked to this agent message"""
        workflow_ids = self.get_agent_linked_workflow_ids(id)
        if workflow_ids:
            return (
                self.session.query(WorkflowMessageModel)
                .filter(WorkflowMessageModel.id.in_(workflow_ids))
                .all()
            )
        return []

    def get_agent_workflow_result_message(self, id: str) -> Optional[WorkflowMessageModel]:
        """get the workflow result message (assumes only one exists)"""
        workflow_messages = self.get_agent_workflow_messages(id)
        if len(workflow_messages) != 1:
            raise ValueError("The agent message received no or multiple workflow result messages.")
        return workflow_messages[0] if workflow_messages else None
