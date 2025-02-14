from unittest import mock

import pytest

from app.core.model.job import Job
from app.core.model.job_graph import JobGraph
from app.core.model.job_result import JobResult
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.service.job_service import JobService


def test_job_wrapper_init():
    """Test JobWrapper init method."""
    wrapper = JobWrapper()
    assert isinstance(wrapper._job_service, JobService)
    assert wrapper._job_service is JobService.instance


def test_job_wrapper_get_job_graph(mocker):
    """Test get_job_graph method."""
    wrapper = JobWrapper()
    # mock wrapper._job_service
    mock_job_service = mocker.patch.object(wrapper, "_job_service", autospec=True)

    test_job_id = "test_job_id"
    mock_job_graph_result = mock.create_autospec(JobGraph)
    mock_job_service.get_job_graph.return_value = mock_job_graph_result

    job_graph = wrapper.get_job_graph(test_job_id)

    assert job_graph == mock_job_graph_result
    mock_job_service.get_job_graph.assert_called_once_with(job_id=test_job_id)


def test_job_wrapper_get_job(mocker):
    """Test get_job method."""
    wrapper = JobWrapper()
    # mock wrapper._job_service
    mock_job_service = mocker.patch.object(wrapper, "_job_service", autospec=True)

    test_original_job_id = "test_original_job_id"
    test_job_id = "test_job_id"
    mock_job_result = mock.create_autospec(Job)
    mock_job_service.get_job.return_value = mock_job_result

    job = wrapper.get_job(test_original_job_id, test_job_id)

    assert job == mock_job_result
    mock_job_service.get_job.assert_called_once_with(
        original_job_id=test_original_job_id, job_id=test_job_id
    )


@pytest.mark.asyncio
async def test_job_wrapper_execute_job(mocker):
    """Test execute_job method."""
    wrapper = JobWrapper()
    # mock wrapper._job_service
    mock_job_service = mocker.patch.object(wrapper, "_job_service", autospec=True)

    mock_job_instance = mock.create_autospec(Job)

    await wrapper.execute_job(mock_job_instance)

    mock_job_service.execute_job.assert_called_once_with(job=mock_job_instance)


@pytest.mark.asyncio
async def test_job_wrapper_query_job_result(mocker):
    """Test query_job_result method."""
    wrapper = JobWrapper()
    # mock wrapper._job_service
    mock_job_service = mocker.patch.object(wrapper, "_job_service", autospec=True)

    test_job_id = "test_job_id"
    mock_job_result_instance = mock.create_autospec(JobResult)
    mock_job_service.query_job_result.return_value = mock_job_result_instance

    job_result = await wrapper.query_job_result(test_job_id)

    assert job_result == mock_job_result_instance
    mock_job_service.query_job_result.assert_called_once_with(job_id=test_job_id)
