from unittest import mock

import pytest

from app.core.common.type import JobStatus
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.sdk.wrapper.session_wrapper import SessionWrapper
from app.core.service.job_service import JobService
from app.core.service.session_service import SessionService


def test_session_wrapper_init():
    """Test session wrapper init method."""
    wrapper = SessionWrapper()
    assert isinstance(wrapper._session_service, SessionService)
    assert wrapper._session_service is SessionService.instance


def test_session_wrapper_session():
    """Test session method."""
    wrapper = SessionWrapper()
    # mock _session_service
    mock_session_service = mock.patch.object(wrapper, "_session_service", autospec=True).start()
    mock_session_instance = mock_session_service.get_session.return_value
    mock_session_instance.id = "test_session_id"

    wrapper_returned, session_id_returned = wrapper.session("test_session_id")

    assert wrapper_returned is wrapper
    assert session_id_returned == "test_session_id"
    mock_session_service.get_session.assert_called_once_with(session_id="test_session_id")

    # Test session method without session_id (None)
    wrapper_returned_none, session_id_returned_none = wrapper.session()

    assert wrapper_returned_none is wrapper
    assert session_id_returned_none == "test_session_id"
    mock_session_service.get_session.assert_called_with(session_id=None)


@pytest.mark.asyncio
async def test_session_wrapper_submit(mocker):
    """Test submit method."""
    JobService()
    wrapper = SessionWrapper()

    # mock JobService.execute_job method
    mock_execute_job_method = mocker.patch(
        "app.core.sdk.wrapper.session_wrapper.JobService.instance.execute_job",
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

    job = await wrapper.submit(test_session_id, mock_chat_message)

    assert isinstance(job, Job)
    assert job.session_id == test_session_id
    assert job.goal == test_message_payload
    mock_execute_job_method.assert_called_once()
    call_args = mock_execute_job_method.call_args
    job_arg = call_args[1]["job"]
    assert isinstance(job_arg, Job)
    assert job_arg.session_id == test_session_id
    assert job_arg.goal == test_message_payload
    mock_asyncio_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_session_wrapper_wait(mocker):
    """Test wait method - simulate result after a few calls using side_effect."""
    JobService()
    wrapper = SessionWrapper()

    # mock JobService.query_job_result method with side_effect
    call_count = 0

    async def mock_query_job_result_side_effect(job_id: str):
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

    mock_query_job_result_method = mocker.patch(
        "app.core.sdk.wrapper.session_wrapper.JobService.query_job_result",
        new_callable=mock.AsyncMock,
        side_effect=mock_query_job_result_side_effect,
    )

    # mock asyncio.sleep
    mock_asyncio_sleep = mocker.patch(
        "app.core.sdk.wrapper.session_wrapper.asyncio.sleep",
        new_callable=mock.AsyncMock,
    )

    test_job_id = "test_job_id"
    test_interval = 10

    result_message = await wrapper.wait(test_job_id, interval=test_interval)

    assert isinstance(result_message, ChatMessage)
    assert result_message.get_payload() == "test result after wait"  # ✅ 验证模拟的 result payload
    mock_asyncio_sleep.assert_called()
    mock_query_job_result_method.assert_called()
    mock_query_job_result_method.assert_called_with(job_id=test_job_id)
