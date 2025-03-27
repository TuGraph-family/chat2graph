from unittest import mock

import pytest

from app.core.common.type import WorkflowPlatformType
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper
from app.core.workflow.operator import Operator
from app.core.workflow.workflow import BuiltinWorkflow
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow


class TestOperator(Operator):
    """Test operator class."""

    def __init__(self, id: str):
        self.id = id


class TestOperatorWrapper(OperatorWrapper):
    """Test operator wrapper class."""

    def __init__(self, operator: Operator):
        self._operator = operator


@pytest.fixture()
def mock_builtin_workflow(mocker):
    """Fixture to mock BuiltinWorkflow class."""
    mocked_builtin_workflow_class = mocker.patch(
        "app.core.sdk.wrapper.workflow_wrapper.BuiltinWorkflow", autospec=True
    )
    return mocked_builtin_workflow_class.return_value


@pytest.fixture()
def mock_dbgpt_workflow(mocker):
    """Fixture to mock DbgptWorkflow class."""
    mocked_dbgpt_workflow_class = mocker.patch(
        "app.plugin.dbgpt.dbgpt_workflow.DbgptWorkflow", autospec=True
    )
    return mocked_dbgpt_workflow_class.return_value


def test_workflow_wrapper_init_default(mock_builtin_workflow: BuiltinWorkflow):
    """Test WorkflowWrapper init with default platform (BuiltinWorkflow)."""
    wrapper = WorkflowWrapper()
    assert isinstance(wrapper.workflow, BuiltinWorkflow)
    wrapper = WorkflowWrapper(workflow=mock_builtin_workflow)
    assert wrapper.workflow == mock_builtin_workflow


def test_workflow_wrapper_init_dbgpt():
    """Test WorkflowWrapper init with DBGPT platform (DbgptWorkflow)."""
    wrapper = WorkflowWrapper(WorkflowPlatformType.DBGPT)
    assert isinstance(wrapper.workflow, DbgptWorkflow)


def test_workflow_wrapper_chain_single_operator(mock_dbgpt_workflow: DbgptWorkflow):
    """Test chain method with a single operator."""
    wrapper = WorkflowWrapper(WorkflowPlatformType.DBGPT)
    wrapper._workflow = mock_dbgpt_workflow

    operator_wrapper = TestOperatorWrapper(TestOperator(id="test_operator_id"))

    # call the chain method with a single operator
    wrapper_returned = wrapper.chain(operator_wrapper)

    assert wrapper_returned.workflow == mock_dbgpt_workflow
    mock_dbgpt_workflow.add_operator.assert_called_once_with(operator_wrapper.operator)


def test_workflow_wrapper_chain_two_operators(mock_dbgpt_workflow: DbgptWorkflow):
    """Test chain method with multiple operators in a tuple."""
    wrapper = WorkflowWrapper(WorkflowPlatformType.DBGPT)
    wrapper._workflow = mock_dbgpt_workflow

    operator_1 = TestOperator(id="test_operator_id_1")
    operator_2 = TestOperator(id="test_operator_id_2")

    operator_wrappers_tuple = (TestOperatorWrapper(operator_1), TestOperatorWrapper(operator_2))
    wrapper_returned = wrapper.chain(operator_wrappers_tuple)

    assert wrapper_returned.workflow == mock_dbgpt_workflow
    assert mock_dbgpt_workflow.add_operator.call_count == 2
    mock_dbgpt_workflow.add_operator.assert_has_calls(
        [
            mock.call(operator_1, next_ops=[operator_2]),
            mock.call(operator_2, previous_ops=[operator_1]),
        ]
    )


def test_workflow_wrapper_chain_multiple_operators(mock_builtin_workflow: DbgptWorkflow):
    """Test chain method with multiple operators."""
    wrapper = WorkflowWrapper(WorkflowPlatformType.DBGPT)
    wrapper._workflow = mock_builtin_workflow

    operator_1 = TestOperator(id="test_operator_id_1")
    operator_2 = TestOperator(id="test_operator_id_2")
    operator_3 = TestOperator(id="test_operator_id_3")

    # call the chain method with multiple operators
    operator_wrappers_tuple = (
        TestOperatorWrapper(operator_1),
        TestOperatorWrapper(operator_2),
        TestOperatorWrapper(operator_3),
    )
    wrapper_returned = wrapper.chain(operator_wrappers_tuple)

    assert wrapper_returned.workflow == mock_builtin_workflow
    assert mock_builtin_workflow.add_operator.call_count == 4
    mock_builtin_workflow.add_operator.assert_has_calls(
        [
            mock.call(operator_1, next_ops=[operator_2]),
            mock.call(operator_2, previous_ops=[operator_1]),
            mock.call(operator_2, next_ops=[operator_3]),
            mock.call(operator_3, previous_ops=[operator_2]),
        ]
    )


def test_workflow_wrapper_chain_invalid_item():
    """Test chain method raises ValueError for invalid item."""
    wrapper = WorkflowWrapper(WorkflowPlatformType.DBGPT)
    with pytest.raises(ValueError) as excinfo:
        wrapper.chain("invalid item")  # type: ignore
    assert "Invalid chain item" in str(excinfo.value)


def test_workflow_wrapper_add_operator_not_implemented():
    """Test add_operator method raises NotImplementedError."""
    wrapper = WorkflowWrapper(WorkflowPlatformType.DBGPT)
    operator_instance = mock.create_autospec(Operator)
    with pytest.raises(NotImplementedError) as excinfo:
        wrapper.add_operator(operator_instance)
    assert "This method is not implemented" in str(excinfo.value)


def test_workflow_wrapper_update_operator(mock_dbgpt_workflow: DbgptWorkflow):
    """Test update_operator method."""
    wrapper = WorkflowWrapper(WorkflowPlatformType.DBGPT)
    wrapper._workflow = mock_dbgpt_workflow

    operator = TestOperator(id="test_operator_id")

    wrapper_returned = wrapper.update_operator(operator)

    assert wrapper_returned.workflow == wrapper.workflow
    mock_dbgpt_workflow.update_operator.assert_called_once_with(operator)


def test_workflow_wrapper_remove_operator_not_implemented():
    """Test remove_operator method raises NotImplementedError."""
    wrapper = WorkflowWrapper(WorkflowPlatformType.DBGPT)
    operator_instance = mock.create_autospec(Operator)
    with pytest.raises(NotImplementedError) as excinfo:
        wrapper.remove_operator(operator_instance)
    assert "This method is not implemented" in str(excinfo.value)
