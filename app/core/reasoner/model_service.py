from abc import ABC, abstractmethod
import inspect
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from app.core.model.message import ModelMessage
from app.core.toolkit.tool import FunctionCallResult, Tool


class ModelService(ABC):
    """Model service."""

    def __init__(self):
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
        func_calls, err = self._parse_function_calls(model_response_text)
        if err:
            return [FunctionCallResult.error(err)]

        if not func_calls:
            # do not call any functions
            return None

        func_call_results: List[FunctionCallResult] = []
        for func_name, call_objective, func_args in func_calls:
            func = self._find_function(func_name, tools)
            if not func:
                func_call_results.append(
                    FunctionCallResult(
                        func_name=func_name,
                        call_objective=call_objective,
                        func_args=func_args,
                        status="failed",
                        output=f"Error: Function {func_name} does not exist in the current scope. "
                        "You have called a function that does not exist in the system, "
                        "and have made a mistake of function calling.",
                    )
                )
                continue

            try:
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
                        status="succeeded",
                        output=str(result),
                    )
                )
            except Exception as e:
                func_call_results.append(
                    FunctionCallResult(
                        func_name=func_name,
                        call_objective=call_objective,
                        func_args=func_args,
                        status="failed",
                        output=f"Function {func_name} execution failed: {str(e)}",
                    )
                )

        return func_call_results

    def _parse_function_calls(
        self, text: str
    ) -> Tuple[List[Tuple[str, str, Dict[str, Any]]], Optional[str]]:
        """Parse function calls from message ctextontent."""
        # calling format: <function_call>name(arg1=value1, arg2=value2)</function_call>
        pattern = r"<function_call>(.*?)</function_call>"
        matches = re.finditer(pattern, text, re.DOTALL)

        if not matches:
            # did not call any functions
            return [], None

        func_calls: List[Tuple[str, str, Dict[str, Any]]] = []
        err: Optional[str] = None
        for match in matches:
            try:
                func_str: str = match.group(1)
                func_data = json.loads(func_str)
                func_name: str = func_data.get("name", "")
                call_objective: str = func_data.get("call_objective", "")
                func_args: Dict[str, Any] = func_data.get("args", {})
                func_calls.append((func_name, call_objective, func_args))
            except Exception as e:
                print(f"Error json parsing, the json format is not validated: {str(e)}")
                err = f"Error json parsing, the json format is not validated: {str(e)}"
                continue

        return func_calls, err

    def _find_function(self, func_name: str, tools: List[Tool]) -> Optional[Callable[..., Any]]:
        """Find matching function from the provided list."""
        for tool in tools:
            if tool.name == func_name:
                return tool.function
        return None
