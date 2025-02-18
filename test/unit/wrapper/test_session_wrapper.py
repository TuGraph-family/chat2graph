from unittest import mock

import pytest

from app.core.common.type import JobStatus
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.model.session import Session
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.sdk.wrapper.session_wrapper import SessionWrapper
from app.core.service.job_service import JobService
from app.core.service.session_service import SessionService


def test_session_wrapper_init():
    """Test session wrapper init method."""
    wrapper = SessionWrapper()
    assert wrapper._session is None


def test_session_wrapper_session(mocker):
    """Test session method."""
    SessionService()
    wrapper = SessionWrapper()

    # mock get_session method
    mock_get_session_method = mocker.patch(
        "app.core.sdk.wrapper.session_wrapper.SessionService.get_session",
        new_callable=mock.Mock,
    )
    mock_session = mock.create_autospec(Session)
    mock_session.id = "test_session_id"
    mock_get_session_method.return_value = mock_session

    # test session method with session_id
    wrapper_returned = wrapper.session("test_session_id")

    assert wrapper_returned is wrapper
    assert wrapper._session == mock_session
    assert wrapper._session.id == "test_session_id"
    mock_get_session_method.assert_called_once_with(session_id="test_session_id")

    # test session method without session_id (None)
    wrapper_returned_none = wrapper.session()

    assert wrapper_returned_none is wrapper
    assert wrapper._session == mock_session
    mock_get_session_method.assert_called_with(session_id=None)


@pytest.mark.asyncio
async def test_session_wrapper_submit(mocker):
    """Test submit method."""
    JobService()
    SessionService()
    wrapper = SessionWrapper()

    wrapper.session("test_session_id")

    # mock JobService.execute_job method
    mock_execute_job_method = mocker.patch(
        "app.core.sdk.wrapper.session_wrapper.JobWrapper.execute",
        new_callable=mock.AsyncMock,
    )
    # mock asyncio.create_task
    mock_asyncio_create_task = mocker.patch(
        "app.core.sdk.wrapper.session_wrapper.asyncio.create_task"
    )

    test_session_id = "test_session_id"
    test_message_payload = "test message payload"
    mock_chat_message: ChatMessage = mock.create_autospec(ChatMessage)
    mock_chat_message.get_payload.return_value = test_message_payload

    job_wrapper = await wrapper.submit(mock_chat_message)

    assert isinstance(job_wrapper, JobWrapper)
    assert job_wrapper.job.session_id == test_session_id
    assert job_wrapper.job.goal == test_message_payload
    mock_execute_job_method.assert_called_once_with()
    mock_asyncio_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_session_wrapper_wait(mocker):
    """Test wait method - simulate result after a few calls using side_effect."""
    JobService()
    wrapper = SessionWrapper()

    # mock JobService.query_job_result method with side_effect
    call_count = 0

    async def mock_result_side_effect():
        nonlocal call_count
        call_count += 1
        mock_job_result: JobResult = mock.create_autospec(JobResult)
        if call_count >= 3:
            # simulate that the job is finished after 3 calls
            mock_job_result.status = JobStatus.FINISHED
            mock_job_result.result = ChatMessage(payload="test result after wait")
        else:
            # simulate that the job is still running
            mock_job_result.status = JobStatus.RUNNING
            mock_job_result.result = None
        return mock_job_result

    mock_result_method = mocker.patch(
        "app.core.sdk.wrapper.session_wrapper.JobWrapper.result",
        new_callable=mock.AsyncMock,
        side_effect=mock_result_side_effect,
    )

    # mock asyncio.sleep
    mock_asyncio_sleep = mocker.patch(
        "app.core.sdk.wrapper.session_wrapper.asyncio.sleep",
        new_callable=mock.AsyncMock,
    )

    test_job_wrapper = JobWrapper(job=Job(goal="test goal"))
    test_interval = 10

    result_message = await wrapper.wait(test_job_wrapper, interval=test_interval)

    assert isinstance(result_message, ChatMessage)
    assert result_message.get_payload() == "test result after wait"
    mock_asyncio_sleep.assert_called()
    mock_result_method.assert_called()
