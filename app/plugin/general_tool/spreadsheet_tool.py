import traceback

import pandas as pd

from app.core.toolkit.tool import Tool


class SpreadsheetTool(Tool):
    """A tool to read data from spreadsheet files (XLSX, CSV)."""

    def __init__(self):
        super().__init__(
            name=self.read_sheet.__name__,
            description=self.read_sheet.__doc__ or "",
            function=self.read_sheet,
        )

    async def read_sheet(self, file_path: str) -> str:
        """Reads data from a spreadsheet and returns it as a string.

        Args:
            file_path (str): The local path to the .xlsx or .csv file.

        Returns:
            A string representation of the spreadsheet data, or an error message.
        """
        try:
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith(".xlsx"):
                df = pd.read_excel(file_path, engine="openpyxl")
            else:
                return "--- ERROR: Unsupported file type. Please provide a .csv or .xlsx file. ---"

            # to_string() is great for LLM readability
            return df.to_string()

        except FileNotFoundError:
            return f"--- ERROR: File not found at path: {file_path} ---"
        except Exception:
            error_trace = traceback.format_exc()
            return f"--- FAILED TO READ SPREADSHEET ---\n{error_trace}"
