from typing import Any, Dict

from dbgpt.core.awel import MapOperator  # type: ignore

from app.agent.workflow.operator.operator import Operator


class DbgptMapOperator(MapOperator[Dict[str, Any], Any]):
    """DB-GPT operator"""

    def __init__(self, operator: Operator, **kwargs):
        super().__init__(**kwargs)
        self._operator = operator

    async def map(self, input_value: Dict[str, str]) -> Any:
        """Execute the operator."""
        context = input_value.get("context", "")
        scratchpad = input_value.get("scratchpad", "")
        reasoning_rounds = int(input_value.get("reasoning_rounds", 5))
        print_messages = input_value.get("print_messages", True)

        if isinstance(print_messages, str):
            print_messages = print_messages.lower() == "true"

        return await self._operator.execute(
            context=context,
            scratchpad=scratchpad,
            reasoning_rounds=reasoning_rounds,
            print_messages=print_messages,
        )
