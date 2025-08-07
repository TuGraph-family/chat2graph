import asyncio
import mimetypes
import os
from pathlib import Path
import tempfile
from typing import Optional, Union
from urllib.parse import urlparse

import magic
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
            Optional[Path]: The absolute path to the downloaded file, or None if the download was skipped (e.g. HTML).

        Raises:
            requests.exceptions.RequestException: If a network error occurs.
        """
        temp_file_no_ext_path = None
        save_path_obj = Path(save_path) if save_path else None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            # Run sync requests code in a separate thread to avoid blocking asyncio event loop
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
                # This case handles when content_type is HTML
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")
            raise  # Re-raise exception
        except Exception as e:
            print(f"An unexpected critical error occurred for url {url}: {e}")
            if temp_file_no_ext_path and os.path.exists(temp_file_no_ext_path):
                os.remove(temp_file_no_ext_path)
            raise  # re-raise exception

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


async def main():
    """Main function to test the UrlDownloaderTool."""
    downloader = UrlDownloaderTool()
    save_dir = Path("./.gaia_tmp")
    save_dir.mkdir(exist_ok=True)

    print("\n--- Testing HTML Page (Should be skipped) ---")
    url_html = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    try:
        path_html = await downloader.download_file_from_url(url_html, save_dir)
        if path_html:
            print(
                f"ERROR: HTML page was downloaded to {path_html}, but it should have been skipped."
            )
            if os.path.exists(path_html):
                os.remove(path_html)
        else:
            print("SUCCESS: HTML page download was correctly skipped.")
    except requests.exceptions.RequestException:
        print(
            "SUCCESS: Download failed due to a network error, as can happen, and was correctly handled."
        )
    except Exception as e:
        print(f"ERROR: An unexpected exception occurred: {e}")

    print("\n--- Testing Direct PDF Download ---")
    url_pdf = "https://arxiv.org/pdf/1706.03762.pdf"  # Attention is All You Need
    try:
        path_pdf = await downloader.download_file_from_url(url_pdf, save_dir)
        if path_pdf:
            print(f"SUCCESS: File saved at: {path_pdf}")
        else:
            print("ERROR: PDF download failed, but no exception was thrown.")
    except Exception as e:
        print(f"ERROR: PDF download failed with an exception: {e}")

    print("\n--- Testing Direct PNG Download ---")
    url_png = "https://www.python.org/static/community_logos/python-logo-master-v3-TM.png"
    try:
        path_png = await downloader.download_file_from_url(url_png, save_dir)
        if path_png:
            print(f"SUCCESS: File saved at: {path_png}")
        else:
            print("ERROR: PNG download failed, but no exception was thrown.")
    except Exception as e:
        print(f"ERROR: PNG download failed with an exception: {e}")

    print(f"\nCheck the '{save_dir.resolve()}' directory for downloaded files.")


if __name__ == "__main__":
    asyncio.run(main())