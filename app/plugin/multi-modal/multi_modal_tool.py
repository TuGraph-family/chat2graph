import base64
import mimetypes
from pathlib import Path
from typing import Any, Dict, List

import litellm

from app.core.common.system_env import SystemEnv
from app.core.toolkit.tool import Tool


class MultiModalTool(Tool):
    """Multi-modal tool for handling various media types using litellm.
    Allows for explicit configuration of API key and base URL.
    """

    def __init__(self):
        super().__init__(
            name="MultiModalTool",
            description="A tool for multi-modal content processing",
            function=self.call_multi_modal,
        )

    def call_multi_modal(self, query_prompt: str, media_paths: List[str]) -> str:
        """Process multi-modal content based on the media types using a multi-modal model.

        Args:
            query_prompt (str): The query prompt to process.
            media_paths (List[str]): A list containing paths to media files or URLs.
                Supported types include images, videos, audio, and PDFs.
                Example: ["/path/to/image.jpg", "https://.../document.pdf", "gs://.../video.mp4"]

        Returns:
            str: The processed response based on the media types.
        """
        content: List[Dict[str, Any]] = [{"type": "text", "text": query_prompt}]

        for path_or_url in media_paths:
            path_or_url = path_or_url.strip()

            # 1. 判断是远程 URL 还是本地文件
            is_url = path_or_url.startswith(("http://", "https://", "gs://"))

            if is_url:
                # 处理远程 URL
                mime_type, _ = mimetypes.guess_type(path_or_url)
                if not mime_type:
                    # 如果无法猜测，给一个通用类型，或根据需求报错
                    mime_type = "application/octet-stream"

                if mime_type.startswith("image/"):
                    # 对于图片URL，使用 'image_url' 类型
                    content.append({"type": "image_url", "image_url": {"url": path_or_url}})
                else:
                    # 对于非图片URL (如 PDF, video), 使用 'file' 类型和 'file_id'
                    # 这完全匹配官方示例 4 和 5
                    content.append(
                        {"type": "file", "file": {"file_id": path_or_url, "format": mime_type}}
                    )
            else:
                # 处理本地文件路径
                file_path = Path(path_or_url)
                if not file_path.exists():
                    return f"Error: Media file not found at {file_path}"

                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = "application/octet-stream"

                with open(file_path, "rb") as f:
                    base64_data = base64.b64encode(f.read()).decode("utf-8")

                # 构造 Data URI
                data_uri = f"data:{mime_type};base64,{base64_data}"

                if mime_type.startswith("image/"):
                    # 对于本地图片，最佳实践是使用 data URI 放入 'image_url'
                    content.append({"type": "image_url", "image_url": {"url": data_uri}})
                else:
                    # 对于其他本地文件 (audio, pdf), 使用 'file' 和 'file_data'
                    content.append({"type": "file", "file": {"file_data": data_uri}})

        messages = [{"role": "user", "content": content}]

        response = litellm.completion(
            model=SystemEnv.MULTI_MODAL_LLM_NAME,
            messages=messages,
            api_key=SystemEnv.MULTI_MODAL_LLM_APIKEY,
            base_url=SystemEnv.MULTI_MODAL_LLM_ENDPOINT,
        )
        return response.choices[0].message.content
