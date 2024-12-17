import asyncio
import time
from typing import List

from app.agent.reasoner.model_service import ModelService
from app.commom.type import MessageSourceType
from app.memory.message import ModelMessage


# Sample functions for testing
def sync_add(a: int, b: int) -> int:
    """A synchronous function that adds two numbers.

    Args:
        a: The first number.
        b: The second number.
    """
    return a + b


async def async_multiply(a: int, b: int) -> int:
    """An asynchronous function that multiplies two numbers.

    Args:
        a: The first number.
        b: The second number.
    """
    await asyncio.sleep(0.1)
    return a * b


def process_complex_data(
    data_dict: dict, nested_list: List[dict], config: dict, special_str: str
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
        self, system_prompt: str, messages: List[ModelMessage]
    ) -> ModelMessage:
        """Implement abstract method."""
        return ModelMessage(
            source_type=MessageSourceType.ACTOR,
            content="test",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )


async def main():
    """Main function"""
    model_service = TestModelService()

    test_funcs = [sync_add, async_multiply, process_complex_data]

    # Create test messages with function calls
    test_cases = [
        # test sync function
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            content=(
                '<function_call>{"name": "sync_add", "call_objective": "Add two numbers", '
                '"args": {"a": 1, "b": 2}}</function_call>'
            ),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        # test async function
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            content=(
                '<function_call>{"name": "async_multiply", "call_objective": "Multiply two numbers", '
                '"args": {"a": 2, "b": 3}}</function_call>'
            ),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        # test multiple function calls
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            content='<function_call>{"name": "sync_add", "args": {"a": 2, "b": 3}}</function_call>\n<function_call>{"name": "async_multiply", '
            '"call_objective": "Multiply two numbers", "args": {"a": 4, "b": 6}}</function_call>',
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        # test invalid function
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            content='<function_call>{"name": "invalid_function", "args": {"a": 1, "b": 2}}</function_call>',
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        # test complex fuction call
        ModelMessage(
            source_type=MessageSourceType.MODEL,
            content="""<function_call>{"name": "process_complex_data",
                "call_objective": "Process complex data",
                "args": {
                    "data_dict": {"a": 1, "b": 2},
                    "nested_list": [{"value": 1}, {"value": 2}, {"value": 3}],
                    "config": {"enabled": true},
                    "special_str": "test"
                }}</function_call>""",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
    ]

    for i, test_msg in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")

        func_call_results = await model_service.call_function(
            funcs=test_funcs, model_response_text=test_msg.get_payload()
        )
        if func_call_results:
            for j, result in enumerate(func_call_results, 1):
                print(
                    f"{j}. {result.status} called function {result.func_name}:\n"
                    f"Call objective: {result.call_objective}\n"
                    f"Function Output: {result.output}"
                )
        else:
            print("Function calling response:\nNone")


if __name__ == "__main__":
    asyncio.run(main())
