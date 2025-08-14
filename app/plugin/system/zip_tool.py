import os
import traceback
from typing import Literal, Optional
import zipfile

from app.core.toolkit.tool import Tool


class ZipTool(Tool):
    """A tool for interacting with .zip archives."""

    def __init__(self):
        super().__init__(
            name=self.operate_zip.__name__,
            description=self.operate_zip.__doc__ or "",
            function=self.operate_zip,
        )

    async def operate_zip(
            self,
            file_path: str,
            action: Literal["list", "extract"],
            output_dir: Optional[str] = None
    ) -> str:
        """Performs an action on a zip file.

        Args:
            file_path (str): The local path to the .zip file.
            action (Literal["list", "extract"]): The action to perform:
                - "list": List the contents of the zip file.
                - "extract": Extract all files from the zip file.
            output_dir (Optional[str]): The directory to extract files to.
                Required if action is 'extract'. Defaults to the same directory
                as the zip file if not provided.

        Returns:
            A success message, a list of files, or an error message.
        """
        if action not in ["list", "extract"]:
            return "--- ERROR: Invalid action. Must be 'list' or 'extract'. ---"

        if action == "extract" and not output_dir:
            # default to a directory with the same name as the zip file, without the extension
            output_dir = os.path.splitext(file_path)[0]

        try:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                if action == "list":
                    file_list = zip_ref.namelist()
                    return "Files in archive:\n" + "\n".join(file_list)

                elif action == "extract":
                    assert output_dir is not None, "Output directory must be specified for extraction if action is 'extract'."  # noqa: E501
                    os.makedirs(output_dir, exist_ok=True)
                    zip_ref.extractall(output_dir)
                    return f"Successfully extracted all files to '{output_dir}'."

        except FileNotFoundError:
            return f"--- ERROR: File not found at path: {file_path} ---"
        except zipfile.BadZipFile:
            return f"--- ERROR: The file at {file_path} is not a valid zip file. ---"
        except Exception:
            error_trace = traceback.format_exc()
            return f"--- FAILED TO HANDLE ZIP FILE ---\n{error_trace}"
