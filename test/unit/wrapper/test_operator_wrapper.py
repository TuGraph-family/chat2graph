import pytest

from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.toolkit.action import Action
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig


@pytest.fixture()
def mock_toolkit_service(mocker):
    """Fixture to mock ToolkitService class."""
    mocked_toolkit_service_class = mocker.patch(
        "app.core.toolkit.toolkit.ToolkitService", autospec=True
    )
    return mocked_toolkit_service_class.return_value


@pytest.fixture()
def mock_knowledge_service(mocker):
    """Fixture to mock KnowledgeService class."""
    mocked_knowledge_service_class = mocker.patch(
        "app.core.knowledge.knowlege_service.KnowledgeService", autospec=True
    )
    return mocked_knowledge_service_class.return_value


@pytest.fixture()
def mock_env_service(mocker):
    """Fixture to mock EnvService class."""
    mocked_env_service_class = mocker.patch("app.core.env.env.EnvService", autospec=True)
    return mocked_env_service_class.return_value


@pytest.fixture()
def mock_toolkit(mocker):
    """Fixture to mock Toolkit class."""
    mocked_toolkit_class = mocker.patch("app.core.toolkit.toolkit.Toolkit", autospec=True)
    return mocked_toolkit_class.return_value


def test_operator_wrapper_configuration_methods():
    """test the configuration methods of OperatorWrapper."""
    wrapper = OperatorWrapper()

    # test instruction()
    assert wrapper.instruction("test instruction") is wrapper
    assert wrapper._instruction == "test instruction"

    # test output_schema()
    assert wrapper.output_schema("test schema") is wrapper
    assert wrapper._output_schema == "test schema"

    # test actions()
    actions = [
        Action(id="action_1", name="action_1", description="test action 1"),
        Action(id="action_2", name="action_2", description="test action 2"),
    ]
    assert wrapper.actions(actions) is wrapper
    assert wrapper._actions == actions


def test_operator_wrapper_build_valid_config():
    """test the build method with valid configurations."""
    wrapper = OperatorWrapper()
    wrapper.instruction("test instruction")
    wrapper.output_schema("test schema")
    actions = [Action(id="action_1", name="action_1", description="test action 1")]
    wrapper.actions(actions)

    operator = wrapper.build().operator

    assert isinstance(operator, Operator)
    assert isinstance(operator._config, OperatorConfig)
    assert operator._config.instruction == "test instruction"
    assert operator._config.output_schema == "test schema"
    assert operator._config.actions == actions


def test_operator_wrapper_build_missing_instruction():
    """test build method raises ValueError when instruction is missing."""
    wrapper = OperatorWrapper()
    wrapper.output_schema("test schema")
    wrapper.actions([Action(id="action_1", name="action_1", description="test action 1")])

    with pytest.raises(ValueError) as excinfo:
        wrapper.build()
    assert "Instruction is required." in str(excinfo.value)
