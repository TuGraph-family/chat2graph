import asyncio

from app.core.toolkit.system_tool.gemini_multi_modal_tool import GeminiMultiModalTool


async def main():
    """Main function to demonstrate and test the MultiModalTool."""
    tool = GeminiMultiModalTool()

    test_query = (
        "You have received multiple files and links. Please analyze them in order and provide a detailed summary (do not hallucinate):\n"
        "1. For audio files, please transcribe the content.\n"
        "2. For images, please describe their content in detail.\n"
        "3. For PDF documents, please summarize their core ideas.\n"
        "4. For YouTube videos, please summarize the video content."
    )

    test_media_paths = [
        "./test/benchmark/gaia/.data/2023/validation/99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3.mp3",
        "./test/benchmark/gaia/.data/2023/validation/5b2a14e8-6e59-479c-80e3-4696e8980152.jpg",
        "https://arxiv.org/pdf/1706.03762.pdf",
        # "https://www.youtube.com/watch?v=MRRMOD_NP2U",
        # "https://zh.wikipedia.org/wiki/%E7%8C%AB",  # This link will be skipped as it cannot be downloaded directly
    ]

    print("--- Starting multi-modal test ---")
    result = await tool.call_multi_modal(query_prompt=test_query, media_paths=test_media_paths)
    print("\n--- Final Result ---")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
