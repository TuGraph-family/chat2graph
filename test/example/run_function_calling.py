import asyncio
from typing import List, Optional

from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service import ModelService
from app.core.toolkit.tool import Tool
from test.resource.init_server import init_server

init_server()


class SyncAdd(Tool):
    """A synchronous function that adds two numbers."""

    def __init__(self):
        name = self.sync_add.__name__
        description = self.sync_add.__doc__ or ""
        super().__init__(
            name=name,
            description=description,
            function=self.sync_add,
        )

    def sync_add(self, a: int, b: int) -> int:
        """A synchronous function that adds two numbers.

        Args:
            a: The first number.
            b: The second number.
        """
        return a + b


class AsyncMultiply(Tool):
    """An asynchronous tool that multiplies two numbers."""

    def __init__(self, id: Optional[str] = None):
        name = self.async_multiply.__name__
        description = self.async_multiply.__doc__ or ""
        super().__init__(
            name=name,
            description=description,
            function=self.async_multiply,
        )

    async def async_multiply(self, a: int, b: int) -> int:
        """An asynchronous function that multiplies two numbers.

        Args:
            a: The first number.
            b: The second number.
        """
        await asyncio.sleep(0.1)
        return a * b


class ProcessComplexData(Tool):
    """A tool that processes complex nested data structures."""
    def __init__(self, id: Optional[str] = None):
        name = self.process_complex_data.__name__
        description = self.process_complex_data.__doc__ or ""
        super().__init__(
            name=name,
            description=description,
            function=self.process_complex_data,
        )

    def process_complex_data(
        self, data_dict: dict, nested_list: List[dict], config: dict, special_str: str
    ) -> dict:
        """A function that processes complex nested data structures.

        Args:
            data_dict: A dictionary containing data.
            nested_list: A list of nested dictionaries.
            config: A configuration dictionary.
            special_str: A special string.
        """
        result = {
            "processed_dict": {k.upper(): v for k, v in data_dict.items()},
            "processed_list": [item["value"] for item in nested_list if "value" in item],
            "config_status": "valid" if config.get("enabled") else "invalid",
            "special_str_length": len(special_str),
        }
        return result


class TestModelService(ModelService):
    """Test implementation of ModelService."""

    async def generate(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        tools: Optional[List[Tool]] = None,
    ) -> ModelMessage:
        """Implement abstract method."""
        return ModelMessage(
            source_type=MessageSourceType.ACTOR,
            payload="test",
            job_id=messages[-1].get_job_id(),
            step=messages[-1].get_step() + 1,
        )


async def main():
    """Main function"""
    model_service = TestModelService()

    test_tools = [SyncAdd(), AsyncMultiply(), ProcessComplexData()]

    job_id: str = "test_job_id"

    # Create test messages with function calls
    test_cases = [
        # test sync function
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload=(
                '<function_call>{"name": "sync_add", "call_objective": "Add two numbers", '
                '"args": {"a": 1, "b": 2}}</function_call>'
            ),
            job_id=job_id,
            step=1,
        ),
        # test async function
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload=(
                '<function_call>{"name": "async_multiply", "call_objective": '
                '"Multiply two numbers", "args": {"a": 2, "b": 3}}</function_call>'
            ),
            job_id=job_id,
            step=2,
        ),
        # test multiple function calls
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload='<function_call>{"name": "sync_add", "call_objective": "Add two numbers", '
            '"args": {"a": 2, "b": 3}}</function_call>\n<function_call>{"name": "async_multiply", '
            '"call_objective": "Multiply two numbers", "args": {"a": 4, "b": 6}}</function_call>',
            job_id=job_id,
            step=3,
        ),
        # test invalid function
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload='<function_call>{"name": "invalid_function", "call_objective": '
            '"Call invalid function", "args": {"a": 1, "b": 2}}</function_call>',
            job_id=job_id,
            step=4,
        ),
        # test complex fuction call
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            payload="""<function_call>{"name": "process_complex_data",
                "call_objective": "Process complex data",
                "args": {
                    "data_dict": {"a": 1, "b": 2},
                    "nested_list": [{"value": 1}, {"value": 2}, {"value": 3}],
                    "config": {"enabled": true},
                    "special_str": "test"
                }}</function_call>""",
            job_id=job_id,
            step=5,
        ),
    ]

    for i, test_msg in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")

        func_call_results = await model_service.call_function(
            tools=test_tools, model_response_text=test_msg.get_payload()
        )
        if func_call_results:
            for j, result in enumerate(func_call_results):
                print(
                    f"{j + 1}. {result.status.value} called function {result.func_name}:\n"
                    f"Call objective: {result.call_objective}\n"
                    f"Function Output: {result.output}"
                )
        else:
            print("Function calling response:\nNone")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
