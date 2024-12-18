import inspect
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

from app.memory.message import ModelMessage
from app.toolkit.tool.tool import FunctionCallResult


class ModelService(ABC):
    """Model service."""

    def __init__(self):
        self._id = str(uuid4())

    @abstractmethod
    async def generate(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        funcs: Optional[List[Callable[..., Any]]] = None,
    ) -> ModelMessage:
        """Generate a text given a prompt non-streaming"""

    async def call_function(
        self, funcs: List[Callable], model_response_text: str
    ) -> Optional[List[FunctionCallResult]]:
        """Call functions based on message content.

        Args:
            funcs: List of available functions
            model_response_text: The text containing potential function calls

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
            func = self._find_function(func_name, funcs)
            if not func:
                func_call_results.append(
                    FunctionCallResult(
                        func_name=func_name,
                        call_objective=call_objective,
                        func_args=func_args,
                        status="failed",
                        output=f"Function {func_name} not found.",
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
                func_name: str = func_data["name"]
                call_objective: str = func_data["call_objective"]
                func_args: Dict[str, Any] = func_data["args"]
                func_calls.append((func_name, call_objective, func_args))
            except Exception as e:
                print(f"Error parsing function call: {str(e)}")
                err = f"Error parsing function call: {str(e)}"
                continue

        return func_calls, err

    def _find_function(
        self, func_name: str, funcs: List[Callable]
    ) -> Optional[Callable]:
        """Find matching function from the provided list."""
        for func in funcs:
            if func.__name__ == func_name:
                return func
        return None
