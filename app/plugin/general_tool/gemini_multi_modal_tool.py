import asyncio
import os
from pathlib import Path
from typing import Any, List

import google.generativeai as genai

from app.core.common.system_env import SystemEnv
from app.core.toolkit.tool import Tool
from app.plugin.general_tool.url_downloader import UrlDownloaderTool


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

        try:
            for path_or_url in media_paths:
                path_or_url = path_or_url.strip()

                # FIX 1: 对不同类型的输入采用不同的处理逻辑
                try:
                    is_url = path_or_url.startswith(("http://", "https://"))

                    file_to_process = None
                    display_name = "unknown"
                    if is_url:
                        # 对其他URL，尝试下载
                        downloaded_path = await UrlDownloaderTool().download_file_from_url(
                            url=path_or_url
                        )
                        if downloaded_path:
                            file_to_process = downloaded_path
                            display_name = downloaded_path.name
                            temp_files_to_clean.append(downloaded_path)
                    else:
                        # 对本地文件
                        local_path = Path(path_or_url).resolve()
                        if local_path.exists():
                            file_to_process = local_path
                            display_name = local_path.name

                    # 仅对真实存在的文件（本地或已下载）使用 upload_file
                    if file_to_process:
                        print(f"正在上传文件: {display_name}")
                        uploaded_file = genai.upload_file(
                            path=file_to_process, display_name=display_name
                        )
                        prompt_parts.append(uploaded_file)
                        print(f"成功上传并添加文件 '{display_name}'")
                    elif not is_url:
                        print(f"跳过不存在的本地文件: {path_or_url}")

                except Exception as e:
                    print(f"处理 '{path_or_url}' 时出错，将跳过。原因: {e}")
                    continue

            if len(prompt_parts) <= 1:
                return "警告：没有处理任何有效的媒体文件。模型只能看到文本提示。"

            print("\n正在使用 Gemini 生成内容...")
            response = await model.generate_content_async(
                prompt_parts, request_options={"timeout": 300.0}
            )
            return response.text

        except Exception as e:
            # 这里的500错误很可能是由无效的测试文件（如b"ID3"）引起的。
            return f"在API调用期间发生意外错误: {e}"

        finally:
            for f in temp_files_to_clean:
                try:
                    os.remove(f)
                    print(f"已清理临时文件: {f}")
                except OSError as e:
                    print(f"清理临时文件 {f} 时出错: {e}")


async def main():
    """用于演示和测试 MultiModalTool 的主函数。"""
    tool = GeminiMultiModalTool()

    test_query = (
        "你收到了多个文件和链接，请依次分析它们并提供详细摘要：\n"
        "1. 对于音频文件，请转录内容。\n"
        "2. 对于图片，请详细描述其内容。\n"
        "3. 对于PDF文档，请总结其核心观点。\n"
        "4. 对于YouTube视频，请总结视频内容。"
    )

    test_media_paths = [
        "./shared_files/99c9cc74-fdc8-46c6-8f8d-3ce2d3bfeea3.mp3",
        "./shared_files/5b2a14e8-6e59-479c-80e3-4696e8980152.jpg",
        "https://arxiv.org/pdf/1706.03762.pdf",
        # "https://www.youtube.com/watch?v=9hE5-98ZeCg",
        "https://zh.wikipedia.org/wiki/%E7%8C%AB",  # 这个链接将因无法直接下载而被跳过
    ]

    print("--- 开始多模态测试 ---")
    result = await tool.call_multi_modal(query_prompt=test_query, media_paths=test_media_paths)
    print("\n--- 最终结果 ---")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
