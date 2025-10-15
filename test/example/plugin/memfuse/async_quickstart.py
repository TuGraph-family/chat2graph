import asyncio
import os

from dotenv import load_dotenv
from memfuse import AsyncMemFuse  # type: ignore
from memfuse.llm import AsyncOpenAI  # type: ignore

load_dotenv(override=True)


async def main():
    """Main async function demonstrating MemFuse async APIs."""

    memfuse = AsyncMemFuse()

    try:
        # all context parameters are optional
        # - memories in MemFuse can exist with flexible context combinations
        memory = await memfuse.init(user="alice")

        # you can check the memory identifiers if needed
        print(f"✓ Memory initialized: {memory.user} | Session: {memory.session}")

        # --- Async OpenAI Example ---
        print("\n🤖 --- Async OpenAI Example ---")
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            memory=memory,
        )

        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-5-nano"),
            messages=[{"role": "user", "content": "I'm working on a project about space "
                       "exploration. Can you tell me something interesting about Mars?"}],
        )

        print("OpenAI Response:", response.choices[0].message.content)

        # test follow-up to verify memory is working
        print("\n🔄 --- OpenAI Follow-up Question ---")
        followup_response = await client.chat.completions.create(
            model=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-5-nano"),
            messages=[{"role": "user", "content": "What would be the biggest challenges for humans "
                       "living on that planet?"}],
        )

        print("OpenAI Follow-up:", followup_response.choices[0].message.content)

        # --- Demonstrate Async Memory Operations ---
        print("\n📚 --- Async Memory Operations Example ---")

        # add some messages to memory
        messages_to_add = [
            {"role": "user", "content": "What are the key benefits of async programming?"},
            {"role": "assistant", "content": "Async programming offers several benefits: 1) Better resource utilization by not blocking threads during I/O operations, 2) Improved scalability for handling many concurrent operations, 3) More responsive applications, and 4) Better performance for I/O-bound tasks."}  # noqa: E501
        ]

        add_result = await memory.add(messages_to_add)
        if add_result.get("status") == "success":
            print("✓ Successfully added messages to memory")

        # Query the memory
        query_result = await memory.query("async programming benefits", top_k=3)
        if query_result.get("status") == "success":
            results_count = len(query_result.get("data", {}).get("results", []))
            print(f"✓ Memory query returned {results_count} relevant results")

        # add some knowledge
        knowledge_to_add = [
            "Python's asyncio library is built on the concept of coroutines and event loops.",
            "The async/await syntax in Python was introduced in Python 3.5.",
            "Async programming is particularly useful for I/O-bound and "
            "high-level structured network code."
        ]

        knowledge_result = await memory.add_knowledge(knowledge_to_add)
        if knowledge_result.get("status") == "success":
            print("✓ Successfully added knowledge to memory")

        # query with both messages and knowledge
        comprehensive_query = await memory.query(
            "Python async features",
            top_k=5, include_messages=True,
            include_knowledge=True,
        )
        if comprehensive_query.get("status") == "success":
            results_count = len(comprehensive_query.get("data", {}).get("results", []))
            print(f"✓ Comprehensive query returned {results_count} relevant results")

    finally:
        await memfuse.close()
        print("\n✅ Async MemFuse client closed")


# alternative way using async context manager (recommended)
async def main_with_context_manager():
    """Demonstration using async context manager for automatic cleanup."""

    print("\n🔧 --- Using Async Context Manager ---")
    
    # use async context manager for AsyncMemFuse
    async with AsyncMemFuse() as memfuse:
        memory = await memfuse.init(user="bob", session="async_demo")

        # add a quick message directly (no need for memory context manager)
        await memory.add([
            {"role": "user", "content": "Hello from async context manager!"},
            {"role": "assistant", "content": "Hello! I'm running with proper resource management."}
        ])

        # query the memory
        result = await memory.query("context manager", top_k=2)
        if result.get("status") == "success":
            results_count = len(result.get("data", {}).get("results", []))
            print(f"✓ Memory query returned {results_count} results")

    print("✅ Async context manager automatically closed all resources")


if __name__ == "__main__":
    print("=== MemFuse Async API Quickstart ===")
    print("This example demonstrates how to use MemFuse with async/await syntax.\n")

    # run the main async function
    asyncio.run(main())

    # also demonstrate the context manager approach
    asyncio.run(main_with_context_manager())

    print("\n=== Async Examples Complete ===")
