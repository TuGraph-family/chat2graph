from abc import ABC, abstractmethod
import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from app.core.common.type import FunctionCallStatus
from app.core.common.util import parse_jsons
from app.core.model.message import ModelMessage
from app.core.prompt.model_service import FUNC_CALLING_JSON_GUIDE
from app.core.reasoner.injection_mapping import (
    injection_services_mapping,
    setup_injection_services_mapping,
)
from app.core.toolkit.tool import FunctionCallResult, Tool


class ModelService(ABC):
    """Model service."""

    def __init__(self):
        # setup the injection services mapping (used by function callings)
        setup_injection_services_mapping()

        # TODO: remove this?
        self._id = str(uuid4())

    @abstractmethod
    async def generate(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        tools: Optional[List[Tool]] = None,
    ) -> ModelMessage:
        """Generate a text given a prompt non-streaming"""

    async def call_function(
        self, tools: List[Tool], model_response_text: str
    ) -> Optional[List[FunctionCallResult]]:
        """Call functions based on message content.

        Args:
            tools (List[Tool]): The tools to call
            model_response_text (str): The text containing potential function calls

        Returns:
            ModelMessage: Response message containing function results
        """
        func_calls = self._parse_function_calls(model_response_text)

        if not func_calls:
            # do not call any functions
            return None

        func_call_results: List[FunctionCallResult] = []
        for func_tuple, err in func_calls:
            if err:
                # handle parsing error
                func_call_results.append(FunctionCallResult.error(err))
                continue

            assert isinstance(func_tuple, tuple)
            func_name, call_objective, func_args = func_tuple
            func = self._find_function(func_name, tools)
            if not func:
                if len(tools) == 0:
                    available_funcs_desc = "No function calling available now."
                else:
                    available_funcs_desc = (
                        "The available functions/tools that can be called by <function_call>: ["
                        f"{', '.join([tool.function.__name__ for tool in tools])}]"
                    )
                func_call_results.append(
                    FunctionCallResult(
                        func_name=func_name,
                        call_objective=call_objective,
                        func_args=func_args,
                        status=FunctionCallStatus.FAILED,
                        output=f"Error: Function {func_name} does not exist in the current scope. "
                        "You have called a function that does not exist in the system, "
                        f"and have made a mistake of function calling. {available_funcs_desc}",
                    )
                )
                continue

            try:
                # prepare function arguments:
                # handle the service injection based on sig parameter types.
                # this will auto-inject services from the mapping when a function requires them
                # TODO: handle the case when the function has no type hints
                # TODO: handle the case when the function has default value
                sig = inspect.signature(func)
                for param_name, param in sig.parameters.items():
                    injection_type_found: bool = False
                    param_type: Any = param.annotation
                    # handle the union types
                    if param_type is Union:
                        available_types = getattr(param_type, "__args__", [])
                        for available_type in available_types:
                            # skip None type
                            if available_type is type(None):
                                continue

                            if available_type in injection_services_mapping:
                                func_args[param_name] = injection_services_mapping[available_type]
                                injection_type_found = True
                                break

                    # try to inject service based on parameter type
                    if not injection_type_found:
                        if param_type in injection_services_mapping:
                            func_args[param_name] = injection_services_mapping[param_type]

                # execute function call
                if inspect.iscoroutinefunction(func):
                    result = await func(**func_args)
                else:
                    result = func(**func_args)

                func_call_results.append(
                    FunctionCallResult(
                        func_name=func_name,
                        call_objective=call_objective,
                        func_args=func_args,
                        status=FunctionCallStatus.SUCCEEDED,
                        output=str(result),
                    )
                )
            except Exception as e:
                func_call_results.append(
                    FunctionCallResult(
                        func_name=func_name,
                        call_objective=call_objective,
                        func_args=func_args,
                        status=FunctionCallStatus.FAILED,
                        output=f"Function {func_name} execution failed: {str(e)}",
                    )
                )

        return func_call_results

    def _parse_function_calls(
        self, text: str
    ) -> List[Tuple[Optional[Tuple[str, str, Dict[str, Any]]], Optional[str]]]:
        """Parse function calls from message ctextontent.

        Args:
            text (str): The text content to parse for function calls.

        Returns:
            Tuple[List[Tuple[Optional[Tuple[str, str, Dict[str, Any]]], Optional[str]]]:
                - A list of tuples where each tuple contains, which can be None if error occurs:
                    - func_name (str): The name of the function to call
                    - call_objective (str): The objective of the function call
                    - func_args (Dict[str, Any]): The arguments for the function call
                - Optional error message if parsing fails.
        """
        # calling format: <function_call>name(arg1=value1, arg2=value2)</function_call>
        func_dicts = parse_jsons(
            text=text,
            start_marker="<function_call>",
            end_marker="</function_call>",
        )

        if len(func_dicts) == 0:
            # did not call any functions
            return []

        func_calls: List[Tuple[Optional[Tuple[str, str, Dict[str, Any]]], Optional[str]]] = []
        for func_dict in func_dicts:
            try:
                func_name: str = func_dict.get("name", "")
                call_objective: str = func_dict.get("call_objective", "")
                func_args: Dict[str, Any] = func_dict.get("args", {})
                func_calls.append(((func_name, call_objective, func_args), None))
            except json.JSONDecodeError as e:
                print(
                    "The system is attempting to match the JSON format within the <funciton_call> "
                    "section through string matching, but a matching error has occurred. "
                    "Please ensure that the content inside <funciton_call> can be parsed as JSON.\n"
                    f"{str(e)}\nPlease check the format of the function calling.\n"
                    f"{FUNC_CALLING_JSON_GUIDE}"
                )
                err = (
                    "The system is attempting to match the JSON format within the <funciton_call> "
                    "section through string matching, but a matching error has occurred. "
                    "Please ensure that the content inside <funciton_call> can be parsed as JSON.\n"
                    f"{str(e)}\nPlease check the format of the function calling.\n"
                    f"{FUNC_CALLING_JSON_GUIDE}"
                )
                func_calls.append((None, err))  # append None to indicate this match failed to parse
                continue

        return func_calls

    def _find_function(self, func_name: str, tools: List[Tool]) -> Optional[Callable[..., Any]]:
        """Find matching function from the provided list."""
        for tool in tools:
            if tool.name == func_name:
                return tool.function
        return None
