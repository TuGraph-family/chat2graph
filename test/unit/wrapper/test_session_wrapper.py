from app.core.dal.init_db import init_db
from app.core.sdk.agentic_service import AgenticService
from app.core.sdk.wrapper.session_wrapper import SessionWrapper

AgenticService()
init_db()


def test_session_wrapper_init(mocker):
    """Test session wrapper init method."""
    wrapper = SessionWrapper()

    assert wrapper._session is not None


# TODO: complete the wait method test for job wrapper
# def test_session_wrapper_submit(mocker):
#     """Test submit method."""
#     JobService()
#     SessionService()
#     wrapper = SessionWrapper()

#     wrapper.session("test_session_id")

#     # mock run_in_thread
#     mock_run_in_thread = mocker.patch("app.core.sdk.wrapper.session_wrapper.run_in_thread")

#     test_session_id = "test_session_id"
#     test_message_payload = "test message payload"
#     test_expert_name = "test expert"
#     mock_chat_message: ChatMessage = mock.create_autospec(ChatMessage)
#     mock_chat_message.get_payload.return_value = test_message_payload
#     mock_chat_message.get_assigned_expert_name.return_value = test_expert_name

#     job_wrapper = wrapper.submit(mock_chat_message)

#     assert isinstance(job_wrapper, JobWrapper)
#     assert job_wrapper.job.session_id == test_session_id
#     assert job_wrapper.job.goal == test_message_payload
#     assert job_wrapper.job.assigned_expert_name == test_expert_name
#     mock_run_in_thread.assert_called_once_with(job_wrapper.execute)
