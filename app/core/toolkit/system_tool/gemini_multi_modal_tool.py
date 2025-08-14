import os
from pathlib import Path
from typing import Any, List

import google.generativeai as genai

from app.core.common.system_env import SystemEnv
from app.core.toolkit.system_tool.url_downloader import UrlDownloaderTool
from app.core.toolkit.tool import Tool


class GeminiMultiModalTool(Tool):
    """Multimodal tool for processing various media types using the Google Gemini API."""

    def __init__(self):
        super().__init__(
            name=self.call_multi_modal.__name__,
            description=self.call_multi_modal.__doc__ or "",
            function=self.call_multi_modal,
        )

    async def call_multi_modal(self, query_prompt: str, media_paths: List[str]) -> str:
        """Process multi-modal content (the base model is a multi-modal LLM) based on the media
            types using a multi-modal model.

        Args:
            query_prompt (str): The query prompt to process. It can be a question or instruction,
                just talk to a multi-modal model like you would with a human. It is suggested to ask
                it to think before answering, to avoid hallucinations.
            media_paths (List[str]): A list containing paths to local media files or public URLs.
                - For local files, provide a relative or absolute path.
                - For URLs, the tool will first attempt to download the resource to a temporary
                  local path. It will print the download path upon success. The downloaded file
                  will then be processed. If the urls are not donwloadable, this tool will
                  export the whole web page to PDF and process it by the multi-modal model.
                Supported types include images, videos, audio, and PDFs.
                Example: ["/path/to/image.jpg", "https://arxiv.org/pdf/1301.6961.pdf", "/path/to/video.mp3"]

        Returns:
            str: The processed response from the multi-modal model, or an error message
                 if a file cannot be found or downloaded.
        """  # noqa: E501
        genai.configure(api_key=SystemEnv.MULTI_MODAL_LLM_APIKEY)
        model = genai.GenerativeModel(model_name=SystemEnv.MULTI_MODAL_LLM_NAME)
        prompt_parts: List[Any] = [query_prompt]
        temp_files_to_clean: List[Path] = []
        error_messages: List[str] = []

        try:
            for path_or_url in media_paths:
                path_or_url = path_or_url.strip()

                # handle different types of input with different logic
                try:
                    is_url = path_or_url.startswith(("http://", "https://"))

                    file_to_process = None
                    display_name = "unknown"
                    if is_url:
                        # for other URLs, try to download
                        try:
                            downloaded_path = await UrlDownloaderTool().download_file_from_url(
                                url=path_or_url
                            )
                            if downloaded_path:
                                file_to_process = downloaded_path
                                display_name = downloaded_path.name
                                temp_files_to_clean.append(downloaded_path)
                            else:
                                # if download fails, record the error
                                message = f"Failed to download or process URL: {path_or_url}"
                                print(message)
                                error_messages.append(message)
                        except Exception as e:
                            message = f"Error processing URL '{path_or_url}', skipped. Reason: {e}"
                            print(message)
                            error_messages.append(message)
                            continue
                    else:
                        # for local files
                        local_path = Path(path_or_url).resolve()
                        if local_path.exists():
                            file_to_process = local_path
                            display_name = local_path.name
                        else:
                            # if local file doesn't exist, record the error
                            message = f"Skipping non-existent local file: {path_or_url}"
                            print(message)
                            error_messages.append(message)
                            continue

                    # only use upload_file for files that actually exist (local or downloaded)
                    if file_to_process:
                        print(f"Uploading file: {display_name}")
                        uploaded_file = genai.upload_file(
                            path=file_to_process, display_name=display_name
                        )
                        prompt_parts.append(uploaded_file)
                        print(f"Successfully uploaded and added file '{display_name}'")

                except Exception as e:
                    message = (
                        f"Unexpected error when processing '{path_or_url}', skipped. Reason: {e}"
                    )
                    print(message)
                    error_messages.append(message)
                    continue

            model_response_text = ""
            if len(prompt_parts) > 1:
                print("\nGenerating content with Gemini...")
                response = await model.generate_content_async(
                    prompt_parts, request_options={"timeout": 300.0}
                )

                # check if the response has parts before accessing .text
                if response.parts:
                    model_response_text = response.text
                else:
                    # handle cases where the response is empty (e.g., due to safety filters)
                    message = "Warning: The response from the model is empty."
                    try:
                        candidate = response.candidates[0]
                        finish_reason = candidate.finish_reason.name

                        reason_map = {
                            "STOP": (
                                "The model finished but did not generate any content. "
                                "This might be because the input was unclear or the model had "
                                "no relevant information to provide."
                            ),
                            "MAX_TOKENS": "The response was truncated due to reaching "
                            "the maximum token limit.",
                            "SAFETY": "The model's response was blocked due to safety filters.",
                            "RECITATION": "The response was blocked due to "
                            "containing copyrighted material.",
                            "OTHER": "The model stopped for an unknown reason.",
                        }
                        reason_text = reason_map.get(finish_reason, "Unknown reason")
                        message += f"\nFinish Reason: {finish_reason} - {reason_text}"

                        if finish_reason == "SAFETY" and candidate.safety_ratings:
                            ratings = ", ".join(
                                [
                                    f"{r.category.name}: {r.probability.name}"
                                    for r in candidate.safety_ratings
                                ]
                            )
                            message += f"\nSafety Ratings: {ratings}"
                    except (IndexError, AttributeError):
                        # if details aren't available, just return the basic warning
                        pass
                    model_response_text = message
            else:
                model_response_text = (
                    "Warning: No valid media files were processed. "
                    "The model can only see the text prompt."
                )

            # append any errors that occurred during file processing
            if error_messages:
                error_summary = "\n\n--- Issues During Processing ---\n" + "\n".join(error_messages)
                return model_response_text + error_summary
            else:
                return model_response_text

        except Exception as e:
            return f"An unexpected error occurred during the API call: {e}"

        finally:
            for f in temp_files_to_clean:
                try:
                    os.remove(f)
                    print(f"Cleaned up temporary file: {f}")
                except OSError as e:
                    print(f"Error cleaning up temporary file {f}: {e}")
