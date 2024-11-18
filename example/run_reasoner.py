import asyncio

from app.agent.reasoner.dual_llm import DualLLMReasoner


async def main():
    """Main function to demonstrate the reasoner usage."""
    task = "Tell me a joke."
    reasoner = await DualLLMReasoner.create(task=task)
    assert isinstance(reasoner, DualLLMReasoner)

    await reasoner.infer()


if __name__ == "__main__":
    asyncio.run(main())
