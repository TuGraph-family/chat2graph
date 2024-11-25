import asyncio
from typing import Any, Dict

from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.workflow import DbgptWorkflow


class BaseTestOperator(Operator):
    """Base test operator"""

    async def execute(
        self,
        context: str,
        scratchpad: str = "",
        reasoning_rounds: int = 5,
        print_messages: bool = True,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class UpperOperator(BaseTestOperator):
    """Upper operator"""

    async def execute(
        self,
        context: str,
        scratchpad: str = "",
        reasoning_rounds: int = 5,
        print_messages: bool = True,
    ) -> Dict[str, Any]:
        result = context.upper() if not scratchpad else scratchpad.upper()
        print(f"UpperOperator input - context: {context}, scratchpad: {scratchpad}")
        print(f"UpperOperator output: {result}\n\n")
        return {"scratchpad": result}


class AddPrefixOperator(BaseTestOperator):
    """Add prefix operator"""

    async def execute(
        self,
        context: str,
        scratchpad: str = "",
        reasoning_rounds: int = 5,
        print_messages: bool = True,
    ) -> Dict[str, Any]:
        result = f"Prefix_{scratchpad}"
        print(f"AddPrefixOperator input - context: {context}, scratchpad: {scratchpad}")
        print(f"AddPrefixOperator output: {result}\n\n")
        return {"scratchpad": result}


class AddSuffixOperator(BaseTestOperator):
    """Add suffix operator"""

    async def execute(
        self,
        context: str,
        scratchpad: str = "",
        reasoning_rounds: int = 5,
        print_messages: bool = True,
    ) -> Dict[str, Any]:
        result = f"{scratchpad}_Suffix"
        print(f"AddSuffixOperator input - context: {context}, scratchpad: {scratchpad}")
        print(f"AddSuffixOperator output: {result}\n\n")
        return {"scratchpad": result}


async def test_parallel():
    """Test parallel workflow: Upper -> Join <- Prefix"""
    workflow = DbgptWorkflow()
    workflow._input_data = {"context": "We are testing parallel workflow"}

    op1 = UpperOperator("upper_op")
    op2 = AddPrefixOperator("prefix_op")
    op3 = AddSuffixOperator("merge_op")

    workflow.add_operator(op1)
    workflow.add_operator(op2)
    workflow.add_operator(op3, previous_ops=[op1, op2])

    result = await workflow.execute()
    print(f"Final result: {result}")


async def main():
    """Main function"""
    await test_parallel()


if __name__ == "__main__":
    asyncio.run(main())
