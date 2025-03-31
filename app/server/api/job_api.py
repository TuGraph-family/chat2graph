from flask import Blueprint

from app.server.common.util import make_response
from app.server.manager.job_manager import JobManager

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/<string:job_id>/message", methods=["GET"])
def get_job_message_view(job_id: str):
    """Get message view (including thinking chain) for a specific job.
    Returns the user's question, AI's answer, and thinking chain messages.
    """
    manager = JobManager()

    # get message view data for the job
    message_view_data, message = manager.get_conversation_view(job_id=job_id)

    return make_response(data=message_view_data, message=message)
