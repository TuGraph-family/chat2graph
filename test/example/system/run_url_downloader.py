import asyncio
import os
from pathlib import Path

import requests

from app.plugin.system.url_downloader import UrlDownloaderTool


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