import asyncio
import mimetypes
import os
from pathlib import Path
import tempfile
from typing import Optional, Union
from urllib.parse import urlparse

try:
    import magic  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    magic = None  # type: ignore
import requests

from app.core.toolkit.tool import Tool


class UrlDownloaderTool(Tool):
    """A tool to download files from URLs, and identifying their true file type."""

    def __init__(self):
        super().__init__(
            name=self.download_file_from_url.__name__,
            description=self.download_file_from_url.__doc__ or "",
            function=self.download_file_from_url,
        )

    async def download_file_from_url(
        self, url: str, save_path: Optional[Union[Path, str]] = None
    ) -> Optional[Path]:
        """Downloads a resource from a URL.

        It downloads the file directly, identifies its true MIME type, and saves it with the
        correct file extension. So make sure to provide a valid URL that can be downloaded.
        This tool will not download HTML pages.

        Args:
            url (str): The URL of the resource to download.
            save_path (Optional[Union[Path, str]]): The destination for the downloaded file.
                If None, the file is saved in a system temporary directory.
                Defaults to None.

        Returns:
            Optional[Path]: The absolute path to the downloaded file, or None if the download
            was failed (e.g. HTML).
        """
        temp_file_no_ext_path = None
        save_path_obj = Path(save_path) if save_path else None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"  # noqa: E501
        }

        try:
            # run sync requests code in a separate thread to avoid blocking asyncio event loop
            def sync_requests_call():
                with requests.get(
                    url,
                    allow_redirects=True,
                    timeout=20,
                    headers=headers,
                    stream=True,
                    verify=True,
                ) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("Content-Type", "")

                    if "text/html" in content_type:
                        print(
                            f"URL content type is HTML ('{content_type}'). Download skipped."
                        )
                        return None

                    print(
                        f"Content-Type '{content_type}' is not HTML. Downloading directly."
                    )
                    with tempfile.NamedTemporaryFile(delete=False) as temp_f:
                        for chunk in response.iter_content(chunk_size=8192):
                            temp_f.write(chunk)
                        return temp_f.name

            downloaded_path = await asyncio.to_thread(sync_requests_call)

            if downloaded_path:
                temp_file_no_ext_path = downloaded_path
                mime_type = magic.from_file(temp_file_no_ext_path, mime=True)
                extension = mimetypes.guess_extension(mime_type)

                # extension handling for common binary files
                if not extension:
                    _, ext_from_url = os.path.splitext(urlparse(url).path)
                    extension = ext_from_url if ext_from_url else ".bin"
                final_path_with_ext = self._get_save_path(
                    url, save_path_obj, extension
                )
                os.rename(temp_file_no_ext_path, final_path_with_ext)

                resolved_path = final_path_with_ext.resolve()
                print(f"File successfully downloaded from {url} to {resolved_path}")
                return resolved_path
            else:
                # when content_type is HTML
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")
            raise
        except Exception as e:
            print(f"An unexpected critical error occurred for url {url}: {e}")
            if temp_file_no_ext_path and os.path.exists(temp_file_no_ext_path):
                os.remove(temp_file_no_ext_path)
            raise

    def _get_save_path(
        self, url: str, save_path: Optional[Union[Path, str]], extension: str
    ) -> Path:
        """Determines the final save path for a downloaded file."""
        if save_path:
            user_path = Path(save_path)
            if not user_path.is_absolute():
                user_path = Path(os.getcwd()).joinpath(user_path).resolve()
            if user_path.is_dir():
                user_path.mkdir(parents=True, exist_ok=True)
                parsed_url = urlparse(url)
                base_name = os.path.basename(parsed_url.path) if parsed_url.path else "download"
                file_name = Path(base_name).stem if base_name else "download"
                final_path = user_path / f"{file_name}{extension}"
            else:
                user_path.parent.mkdir(parents=True, exist_ok=True)
                final_path = user_path.with_suffix(extension)
        else:
            temp_dir = tempfile.gettempdir()
            parsed_url = urlparse(url)
            base_name = os.path.basename(parsed_url.path) if parsed_url.path else "download"
            file_name = Path(base_name).stem
            final_path = Path(
                tempfile.mktemp(suffix=extension, prefix=f"{file_name}_", dir=temp_dir)
            )
        return final_path
