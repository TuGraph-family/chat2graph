from typing import Any, Dict, List, Optional, Tuple

from app.core.common.system_env import SystemEnv
from app.core.model.session import Session
from app.core.service.job_service import JobService
from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.service.session_service import SessionService
from app.server.manager.view.message_view import MessageViewTransformer


class SessionManager:
    """Session Manager class to handle business logic"""

    def __init__(self):
        self._session_service: SessionService = SessionService.instance
        self._job_service: JobService = JobService.instance
        self._knowledgebase_service: KnowledgeBaseService = KnowledgeBaseService.instance

    def create_session(self, name: str) -> Tuple[Dict[str, Any], str]:
        """Create a new session and return the response data.

        Args:
            name (str): Name of the session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing session details and success message
        """
        session: Session = self._session_service.create_session(name=name)
        knowledgebase = self._knowledgebase_service.create_knowledge_base(
            name=name,
            knowledge_type=SystemEnv.KNOWLEDGE_STORE_TYPE,
            session_id=session.id,
        )
        data = {
            "id": session.id,
            "knowledgebase_id": knowledgebase.id,
            "name": session.name,
            "timestamp": session.timestamp,
            "latest_job_id": session.latest_job_id,
        }
        return data, "Session created successfully"

    def get_session(self, session_id: str) -> Tuple[Dict[str, Any], str]:
        """Get session details by ID.

        Args:
            session_id (str): ID of the session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing session details and success message
        """
        session = self._session_service.get_session(session_id=session_id)
        data = {
            "id": session.id,
            "name": session.name,
            "timestamp": session.timestamp,
            "latest_job_id": session.latest_job_id,
        }
        return data, "Session fetched successfully"

    def delete_session(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Delete a session by ID.

        Args:
            id (str): ID of the session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing deletion status and success message
        """
        kb = self._knowledgebase_service.get_session_knowledge_base(session_id=id)
        if kb:
            self._knowledgebase_service.clean_knowledge_base(id=kb.id, drop=True)

        self._session_service.delete_session(id=id)
        return {}, f"Session with ID {id} deleted successfully"

    def update_session(self, session: Session) -> Tuple[Dict[str, Any], str]:
        """Update a session's name by ID."""
        updated_session = self._session_service.update_session(session=session)
        data = {
            "id": updated_session.id,
            "name": updated_session.name,
            "timestamp": updated_session.timestamp,
            "latest_job_id": updated_session.latest_job_id,
        }
        return data, "Session updated successfully"

    def get_all_sessions(
        self, size: Optional[int] = None, page: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Get all sessions.

        Args:
            size (Optional[int]): Number of sessions per page
            page (Optional[int]): Page number for pagination (1-based index)

        Returns:
            Tuple[List[Dict[str, Any]], str]: A tuple containing a list of session details and
                success message
        """
        sessions = self._session_service.get_all_sessions()
        sessions = sorted(sessions, key=lambda session: session.timestamp or 0, reverse=True)
        total_sessions = len(sessions)

        if size and page and size > 0 and page >= 1:
            start_idx = (page - 1) * size
            if start_idx >= total_sessions:
                return [], "No more sessions to fetch, since the page index is too high"
            end_idx = min(start_idx + size, total_sessions)
            message = f"Fetched {end_idx - start_idx} out of {total_sessions} sessions successfully"
        else:
            start_idx = 0
            end_idx = total_sessions
            message = f"Fetched all {total_sessions} sessions successfully"

        session_list = [
            {
                "id": session.id,
                "name": session.name,
                "timestamp": session.timestamp,
                "latest_job_id": session.latest_job_id,
            }
            for session in sessions[start_idx:end_idx]
        ]

        return session_list, message

    def get_all_job_ids(self, session_id: str) -> Tuple[List[str], str]:
        """Get all job IDs for a session.

        Args:
            session_id (str): ID of the session

        Returns:
            Tuple[List[Dict[str, Any]], str]: A tuple containing a list of job IDs and success
                message
        """
        jobs = self._job_service.get_original_jobs_by_session_id(session_id=session_id)
        job_list = [job.id for job in jobs]
        return job_list, "Get all job ids successfully"

    def get_conversation_views(self, session_id: str) -> Tuple[List[Dict[str, Any]], str]:
        """Get all conversation views for a session.

        Args:
            session_id (str): ID of the session

        Returns:
            List[Dict[str, Any]]: List of MessageView objects
        """
        # get all job ids in the session
        job_ids: List[str] = self.get_all_job_ids(session_id=session_id)[0]

        # get message view data for the job
        conversation_views: List[Dict[str, Any]] = []
        for job_id in job_ids:
            conversation_view = self._job_service.get_conversation_view(original_job_id=job_id)
            conversation_views.append(
                MessageViewTransformer.serialize_conversation_view(conversation_view)
            )

        return conversation_views, "Get all conversation views successfully"
