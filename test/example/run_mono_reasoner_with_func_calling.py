import asyncio
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.model.job import SubJob
from app.core.model.task import Task
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.toolkit.tool import Tool


# example tool
class Calculator(Tool):
    """The tool in the toolkit."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.calculator.__name__,
            description=self.calculator.__doc__ or "",
            function=self.calculator,
        )

    async def calculator(self, operation: str, numbers: List[float]) -> Dict[str, Any]:
        """Perform basic math operations.

        Args:
            operation (str): The operation type (add/subtract/multiply/divide/power/sqrt).
            numbers (List[float]): The list of numbers, for example, [1.0, 2.0, 3.0].

        Returns:
            Dict[str, Any]: The calculation result.
        """
        result = 0.0
        if operation == "add":
            result = sum(numbers)
        elif operation == "subtract":
            result = float(numbers[0] - sum(numbers[1:]))
        elif operation == "multiply":
            result = 1
            for num in numbers:
                result *= num
        elif operation == "divide":
            result = numbers[0]
            for num in numbers[1:]:
                result /= num
        elif operation == "power":
            result = numbers[0] ** numbers[1]
        elif operation == "sqrt":
            result = numbers[0] ** 0.5
        return {"result": result}


async def main():
    """Main function."""

    calulation_task = """
===== TASK =====
假设你有一笔投资：
1. 初始投资本金为 10,000 元
2. 年利率为 4.5%
3. 投资期限为 3 年
4. 每年年底额外投资金额为前一年本金的平方根的 50%
5. 利息每年复利计算
请计算：
a) 第一年年底总金额（包括本金、利息和额外投资）
b) 第二年年底总金额
c) 第三年年底总金额
d) 三年总收益率（用百分比表示）
要求：
解决基础数学计算问题，包括但不限于加减乘除、平方根、指数等运算。所有计算都应该显示详细的步骤和推导过程。
"""
    calculation_context = """
===== CONTEXT =====
用户会提供数学计算问题，系统需要：
1. 理解问题类型和要求
2. 展示调用合适的计算工具的过程
"""

    reasoner = MonoModelReasoner()

    job = SubJob(goal="goal", context=calulation_task + calculation_context)
    task = Task(job=job, tools=[Calculator()])

    await reasoner.infer(task=task)


if __name__ == "__main__":
    asyncio.run(main())
