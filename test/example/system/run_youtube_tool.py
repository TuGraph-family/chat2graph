import asyncio

from app.plugin.system.youtube_tool import YouTubeTool


async def main():
    """Main function to demonstrate and test the YouTubeTool."""
    tool = YouTubeTool()

    test_query_1 = "Summarize the main points of this video."
    test_youtube_url = "https://www.youtube.com/watch?v=9hE5-98ZeCg"

    print("--- Test 1: Basic Analysis ---")
    result_1 = await tool.watch_youtube(query_prompt=test_query_1, youtube_url=test_youtube_url)
    print("\n--- Final Result 1 ---")
    print(result_1)

    print("\n" + "=" * 40 + "\n")

    test_query_2 = "What is happening in this segment of the video?"

    print("--- Test 2: Analysis with Time Offsets ---")
    result_2 = await tool.watch_youtube(
        query_prompt=test_query_2,
        youtube_url=test_youtube_url,
        start_offset="10s",
        end_offset="25s",
    )
    print("\n--- Final Result 2 ---")
    print(result_2)


if __name__ == "__main__":
    asyncio.run(main())
