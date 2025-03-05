import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session as SessionType

from app.core.dal.dao.dao import DAO
from app.core.dal.model.message_model import (
    AgentMessageModel,
    ChatMessageModel,
    MessageModel,
    ModelMessageModel,
    TextMessageModel,
    WorkflowMessageModel,
)


class MessageDAO(DAO[MessageModel]):
    """message base dao"""

    def __init__(self, session: SessionType):
        super().__init__(MessageModel, session)

    def get_by_time_range(self, start_time: str, end_time: str) -> List[MessageModel]:
        """get messages by time range"""
        return (
            self._session.query(self._model)
            .filter(self._model.timestamp >= start_time, self._model.timestamp <= end_time)
            .all()
        )

    def get_by_type(self, type: str) -> List[MessageModel]:
        """get messages by type"""
        return self._session.query(self._model).filter(self._model.type == type).all()


class ModelMessageDAO(DAO[ModelMessageModel]):
    """model message dao"""

    def __init__(self, session: SessionType):
        super().__init__(ModelMessageModel, session)

    def get_by_source_type(self, source_type: str) -> List[ModelMessageModel]:
        """get model messages by source type"""
        return self._session.query(self._model).filter(self._model.source_type == source_type).all()

    def get_by_session(self, session_id: str) -> List[ModelMessageModel]:
        """get model messages by session id"""
        return self._session.query(self._model).filter(self._model.session_id == session_id).all()

    def get_by_job(self, job_id: str) -> List[ModelMessageModel]:
        """get model messages by job id"""
        return self._session.query(self._model).filter(self._model.job_id == job_id).all()

    def get_by_operator(self, operator_id: str) -> List[ModelMessageModel]:
        """get model messages by operator id"""
        return self._session.query(self._model).filter(self._model.operator_id == operator_id).all()

    def get_by_step(self, step: str) -> List[ModelMessageModel]:
        """get model messages by step"""
        return self._session.query(self._model).filter(self._model.step == step).all()

    def get_payload(self, id: str) -> Optional[str]:
        """get message content"""
        message = self.get_by_id(id)
        return message.payload if message else None

    def get_function_calls(self, id: str) -> Optional[List]:
        """get function calls"""
        message = self.get_by_id(id)
        if message and message.function_calls_json:
            return json.loads(message.function_calls_json)
        return None

    def update_function_calls(self, id: str, function_calls: List) -> Optional[ModelMessageModel]:
        """update function calls"""
        return self.update(id, function_calls_json=json.dumps(function_calls))


class WorkflowMessageDAO(DAO[WorkflowMessageModel]):
    """workflow message dao"""

    def __init__(self, session: SessionType):
        super().__init__(WorkflowMessageModel, session)

    def get_payload(self, id: str) -> Optional[Dict]:
        """get message payload"""
        message = self.get_by_id(id)
        if message and message.payload_json:
            return json.loads(message.payload_json)
        return None

    def get_attribute(self, id: str, attr_name: str) -> Any:
        """get dynamic attribute value"""
        payload = self.get_payload(id)
        return payload.get(attr_name) if payload else None

    def set_attribute(
        self, id: str, attr_name: str, attr_value: Any
    ) -> Optional[WorkflowMessageModel]:
        """set dynamic attribute value"""
        message = self.get_by_id(id)
        if message:
            payload = json.loads(message.payload_json) if message.payload_json else {}
            payload[attr_name] = attr_value
            message.payload_json = json.dumps(payload)
            self._session.commit()
        return message

    def update_payload(
        self, id: str, new_payload: Dict[str, Any]
    ) -> Optional[WorkflowMessageModel]:
        """update entire payload"""
        return self.update(id, payload_json=json.dumps(new_payload))


class AgentMessageDAO(DAO[AgentMessageModel]):
    """agent message dao"""

    def __init__(self, session: SessionType):
        super().__init__(AgentMessageModel, session)

    def get_by_job_id(self, job_id: str) -> List[AgentMessageModel]:
        """get agent messages by job id"""
        return self._session.query(self._model).filter(self._model.job.id == job_id).all()

    def get_lesson(self, id: str) -> Optional[str]:
        """get lesson content"""
        message = self.get_by_id(id)
        return message.lesson if message else None

    def set_lesson(self, id: str, lesson: str) -> Optional[AgentMessageModel]:
        """set lesson content"""
        return self.update(id, lesson=lesson)

    def get_linked_workflow_ids(self, id: str) -> List[str]:
        """get linked workflow ids"""
        message = self.get_by_id(id)
        if message and message.linked_workflow_ids:
            return json.loads(message.linked_workflow_ids)
        return []

    def set_linked_workflow_ids(
        self, id: str, workflow_ids: List[str]
    ) -> Optional[AgentMessageModel]:
        """set linked workflow ids"""
        return self.update(id, linked_workflow_ids=json.dumps(workflow_ids))

    def add_workflow_message(self, agent_id: str, workflow_id: str) -> None:
        """add a workflow message reference to an agent message"""
        agent_message = self.get_by_id(agent_id)
        if agent_message:
            workflow_ids = self.get_linked_workflow_ids(agent_id)
            if workflow_id not in workflow_ids:
                workflow_ids.append(workflow_id)
                self.set_linked_workflow_ids(agent_id, workflow_ids)

    def remove_workflow_message(self, agent_id: str, workflow_id: str) -> None:
        """remove a workflow message reference from an agent message"""
        agent_message = self.get_by_id(agent_id)
        if agent_message:
            workflow_ids = self.get_linked_workflow_ids(agent_id)
            if workflow_id in workflow_ids:
                workflow_ids.remove(workflow_id)
                self.set_linked_workflow_ids(agent_id, workflow_ids)

    def get_workflow_messages(self, id: str) -> List[WorkflowMessageModel]:
        """get all workflow messages linked to this agent message"""
        workflow_ids = self.get_linked_workflow_ids(id)
        if workflow_ids:
            return (
                self._session.query(WorkflowMessageModel)
                .filter(WorkflowMessageModel.id.in_(workflow_ids))
                .all()
            )
        return []

    def get_workflow_result_message(self, id: str) -> Optional[WorkflowMessageModel]:
        """get the workflow result message (assumes only one exists)"""
        workflow_messages = self.get_workflow_messages(id)
        if len(workflow_messages) != 1:
            raise ValueError("the agent message received no or multiple workflow result messages")
        return workflow_messages[0] if workflow_messages else None


class ChatMessageDAO(DAO[ChatMessageModel]):
    """chat message dao"""

    def __init__(self, session: SessionType):
        super().__init__(ChatMessageModel, session)

    def get_by_session_id(self, session_id: str) -> List[ChatMessageModel]:
        """get chat messages by session id"""
        return self._session.query(self._model).filter(self._model.session_id == session_id).all()

    def get_by_role(self, role: str) -> List[ChatMessageModel]:
        """get chat messages by role"""
        return self._session.query(self._model).filter(self._model.role == role).all()

    def get_by_session_and_role(self, session_id: str, role: str) -> List[ChatMessageModel]:
        """get chat messages by session id and role"""
        return (
            self._session.query(self._model)
            .filter(self._model.session_id == session_id, self._model.role == role)
            .all()
        )

    def get_by_chat_message_type(self, subtype: str) -> List[ChatMessageModel]:
        """get chat messages by subtype"""
        return (
            self._session.query(self._model).filter(self._model.chat_message_type == subtype).all()
        )

    def get_payload(self, id: str) -> Optional[str]:
        """get message content"""
        message = self.get_by_id(id)
        return message.payload if message else None


class TextMessageDAO(DAO[TextMessageModel]):
    """text message dao"""

    def __init__(self, session: SessionType):
        super().__init__(TextMessageModel, session)

    def get_payload(self, id: str) -> Optional[str]:
        """get text content"""
        message = self.get_by_id(id)
        return message.payload if message else None
