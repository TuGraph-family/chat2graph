from unittest import mock

import pytest

from app.core.env.env import EnvService
from app.core.knowledge.knowlege_service import KnowledgeService
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.toolkit.action import Action
from app.core.toolkit.toolkit import Toolkit, ToolkitService
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

    # test service() with ToolkitService
    mock_toolkit_service_instance = mock.create_autospec(ToolkitService)
    assert wrapper.service(mock_toolkit_service_instance) is wrapper
    assert wrapper._toolkit_service == mock_toolkit_service_instance

    # test service() with KnowledgeService
    mock_knowledge_service_instance = mock.create_autospec(KnowledgeService)
    assert wrapper.service(mock_knowledge_service_instance) is wrapper
    assert wrapper._knowledge_service == mock_knowledge_service_instance

    # test service() with EnvService
    mock_env_service_instance = mock.create_autospec(EnvService)
    assert wrapper.service(mock_env_service_instance) is wrapper
    assert wrapper._environment_service == mock_env_service_instance

    # test service() with invalid service
    with pytest.raises(ValueError) as excinfo:
        wrapper.service("invalid service")
    assert "Invalid service" in str(excinfo.value)


def test_operator_wrapper_build_valid_config(
    mock_toolkit_service: ToolkitService,
    mock_knowledge_service: KnowledgeService,
    mock_env_service: EnvService,
):
    """test the build method with valid configurations."""
    wrapper = OperatorWrapper()
    wrapper.instruction("test instruction")
    wrapper.output_schema("test schema")
    actions = [Action(id="action_1", name="action_1", description="test action 1")]
    wrapper.actions(actions)
    wrapper.service(mock_toolkit_service)
    wrapper.service(mock_knowledge_service)
    wrapper.service(mock_env_service)

    operator = wrapper.build()

    assert isinstance(operator, Operator)
    assert isinstance(operator._config, OperatorConfig)
    assert operator._config.instruction == "test instruction"
    assert operator._config.output_schema == "test schema"
    assert operator._config.actions == actions
    assert operator._toolkit_service == mock_toolkit_service
    assert operator._knowledge_service == mock_knowledge_service
    assert operator._environment_service == mock_env_service


def test_operator_wrapper_syntactic_sugar_configuration_methods(mock_toolkit: Toolkit):
    """test the syntactic sugar configuration methods of OperatorWrapper."""
    wrapper = OperatorWrapper()

    # test toolkit_service()
    assert wrapper.toolkit_service(mock_toolkit) is wrapper
    assert isinstance(wrapper._toolkit_service, ToolkitService)
    assert wrapper._toolkit_service._toolkit == mock_toolkit

    # test env_service()
    # TODO: test the env_service method

    # test knowledge_service()
    # TODO: test the knowledge_service method


def test_operator_wrapper_build_missing_instruction(mock_toolkit_service: ToolkitService):
    """test build method raises ValueError when instruction is missing."""
    wrapper = OperatorWrapper()
    wrapper.output_schema("test schema")
    wrapper.actions([Action(id="action_1", name="action_1", description="test action 1")])
    wrapper.service(mock_toolkit_service)

    with pytest.raises(ValueError) as excinfo:
        wrapper.build()
    assert "Instruction is required." in str(excinfo.value)


def test_operator_wrapper_build_missing_output_schema(mock_toolkit_service: ToolkitService):
    """test build method raises ValueError when output_schema is missing."""
    wrapper = OperatorWrapper()
    wrapper.instruction("test instruction")
    wrapper.actions([Action(id="action_1", name="action_1", description="test action 1")])
    wrapper.service(mock_toolkit_service)

    with pytest.raises(ValueError) as excinfo:
        wrapper.build()
    assert "Output schema is required." in str(excinfo.value)


def test_operator_wrapper_build_missing_actions(mock_toolkit_service: ToolkitService):
    """test build method raises ValueError when actions are missing."""
    wrapper = OperatorWrapper()
    wrapper.instruction("test instruction")
    wrapper.output_schema("test schema")
    wrapper.service(mock_toolkit_service)

    with pytest.raises(ValueError) as excinfo:
        wrapper.build()
    assert "Actions are required." in str(excinfo.value)


def test_operator_wrapper_build_missing_toolkit_service():
    """test build method raises ValueError when toolkit_service is missing."""
    wrapper = OperatorWrapper()
    wrapper.instruction("test instruction")
    wrapper.output_schema("test schema")
    wrapper.actions([Action(id="action1", name="action1", description="test action 1")])

    with pytest.raises(ValueError) as excinfo:
        wrapper.build()
    assert "Toolkit service is required." in str(excinfo.value)
