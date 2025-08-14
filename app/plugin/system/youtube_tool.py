from typing import Dict, Optional

from google import genai
from google.genai import types

from app.core.common.system_env import SystemEnv
from app.core.toolkit.tool import Tool


class YouTubeTool(Tool):
    """A multi-modal tool to analyze YouTube videos using Google Gemini."""

    def __init__(self):
        super().__init__(
            name=self.watch_youtube.__name__,
            description=self.watch_youtube.__doc__ or "",
            function=self.watch_youtube,
        )

    async def watch_youtube(
        self,
        query_prompt: str,
        youtube_url: str,
        start_offset: Optional[str] = None,
        end_offset: Optional[str] = None,
    ) -> str:
        """Analyzes a YouTube video from a given URL within an optional specified time range.

        Args:
            query_prompt (str): The prompt or question about the video. It is suggested to ask
                it to think before answering, to avoid hallucinations.
            youtube_url (str): The public URL of the YouTube video.
            start_offset (Optional[str]): The start time for analysis, formatted as a string with 's' suffix (e.g., '60s' for 60 seconds). Defaults to None.
            end_offset (Optional[str]): The end time for analysis, formatted as a string with 's' suffix (e.g., '120s' for 120 seconds). Defaults to None.

        Returns:
            str: A string representing the analysis result from the model.
        """  # noqa: E501
        video_metadata: Dict[str, str] = {}
        if start_offset:
            video_metadata["start_offset"] = start_offset
            print(f"Start Offset: {start_offset}")
        if end_offset:
            video_metadata["end_offset"] = end_offset
            print(f"End Offset: {end_offset}")

        file_data = types.FileData(file_uri=youtube_url)
        metadata = (
            types.VideoMetadata(start_offset=start_offset, end_offset=end_offset)
            if video_metadata
            else None
        )

        client = genai.Client(api_key=SystemEnv.MULTI_MODAL_LLM_APIKEY)
        response = client.models.generate_content(
            model=SystemEnv.MULTI_MODAL_LLM_NAME,
            contents=[
                query_prompt,
                types.Part(file_data=file_data, video_metadata=metadata),
            ],
        )
        result_text = f"Analysis complete for {youtube_url}\n\nAnswer: {response.text}"
        if video_metadata:
            result_text += f" with offsets {video_metadata}."
        else:
            result_text += "."

        return result_text
