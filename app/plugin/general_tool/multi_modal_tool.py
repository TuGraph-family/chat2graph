import asyncio
import base64
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List

import litellm

from app.core.common.system_env import SystemEnv
from app.core.toolkit.tool import Tool
from app.plugin.general_tool.url_downloader import UrlDownloaderTool


class MultiModalTool(Tool):
    """Multi-modal tool for handling various media types using litellm.
    Allows for explicit configuration of API key and base URL.
    """

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
                just talk to a multi-modal model like you would with a human.
            media_paths (List[str]): A list containing paths to local media files or public URLs.
                - For local files, provide a relative or absolute path.
                - For URLs, the tool will first attempt to download the resource to a temporary
                  local path. It will print the download path upon success. The downloaded file
                  will then be processed. If the urls are not donwloadable, this tool will
                  export the whole web page to PDF and process it by the multi-modal model.
                Supported types include images, videos, audio, and PDFs.
                Example: ["/path/to/image.jpg", "https://arxiv.org/pdf/1301.6961.pdf", "https://whitney.org/collection/works/65848"]

        Returns:
            str: The processed response from the multi-modal model, or an error message
                 if a file cannot be found or downloaded.
        """  # noqa: E501
        content: List[Dict[str, Any]] = [{"type": "text", "text": query_prompt}]
        temp_files_to_clean = []

        try:
            for path_or_url in media_paths:
                path_or_url = path_or_url.strip()
                file_path: Path | None = None

                is_url = path_or_url.startswith(("http://", "https://", "gs://"))
                if is_url:
                    # 对于 "gs://" 协议，我们遵循原始逻辑，因为它不是标准的 HTTP 下载
                    if path_or_url.startswith("gs://"):
                        mime_type, _ = mimetypes.guess_type(path_or_url)
                        if not mime_type:
                            mime_type = "application/octet-stream"
                        content.append(
                            {"type": "file", "file": {"file_id": path_or_url, "format": mime_type}}
                        )
                        continue  # 处理完 gs:// URL 后跳过后续的本地文件逻辑

                    # 对于 HTTP/HTTPS URL，下载文件
                    downloaded_path = await UrlDownloaderTool().download_file_from_url(url=path_or_url)
                    if downloaded_path:
                        file_path = downloaded_path
                        temp_files_to_clean.append(file_path)
                    else:
                        return f"Error: Failed to download media from URL: {path_or_url}"
                else:
                    # 处理本地文件路径
                    local_path = Path(path_or_url)
                    if not local_path.is_absolute():
                        local_path = (Path(os.getcwd()) / local_path).resolve()

                    if not local_path.exists():
                        return f"Error: Media file not found at {local_path}"
                    file_path = local_path

                if not file_path:
                    continue

                mime_type, _ = mimetypes.guess_type(file_path.as_uri())
                if not mime_type:
                    mime_type = "application/octet-stream"

                with open(file_path, "rb") as f:
                    base64_data = base64.b64encode(f.read()).decode("utf-8")

                # construct data URI for the file
                data_uri = f"data:{mime_type};base64,{base64_data}"

                if mime_type.startswith("image/"):
                    content.append({"type": "image_url", "image_url": {"url": data_uri}})
                else:
                    content.append({"type": "file", "file": {"file_data": data_uri}})

            if len(content) <= 1:
                return "Error: No valid media content was processed."

            messages = [{"role": "user", "content": content}]

            response = litellm.completion(
                model=SystemEnv.MULTI_MODAL_LLM_NAME,
                messages=messages,
                api_key=SystemEnv.MULTI_MODAL_LLM_APIKEY,
                base_url=SystemEnv.MULTI_MODAL_LLM_ENDPOINT,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: An exception occurred while processing the media files: {str(e)}"

        finally:
            for f in temp_files_to_clean:
                try:
                    os.remove(f)
                    print(f"Cleaned up temporary file: {f}")
                except OSError as e:
                    print(f"Error cleaning up temporary file {f}: {e}")


async def main():
    """Main function to demonstrate the usage of MultiModalTool."""
    result = await MultiModalTool().call_multi_modal(
        query_prompt="请从PDF中提取重要的信息，总结这篇文章",
        media_paths=[
            "./shared_files/67e8878b-5cef-4375-804e-e6291fdbe78a.pdf",
            # "https://arxiv.org/pdf/1301.6961.pdf",
            # "https://threatenedtaxa.org/index.php/JoTT/article/view/3238/4123",
            # "https://whitney.org/collection/works/65848",
            # "https://en.wikipedia.org/w/index.php?title=Ice_cream&action=history",
            # "https://www.bing.com/search?q=what+kind+of+fish+is+nemo",
        ],
    )
    print("Result:", result)


if __name__ == "__main__":
    asyncio.run(main())
