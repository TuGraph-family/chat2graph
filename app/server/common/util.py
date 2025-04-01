import sys
import traceback
from typing import Any, Optional

from flask import jsonify


class ApiException(Exception):
    """Base exception class."""

    def __init__(self, message: str, status_code: int = 400):
        self.message: str = message
        self.status_code: int = status_code


def make_response(data: Optional[Any] = None, message: str = "") -> Any:
    """Create a JSON response."""
    response = {"success": True, "data": data, "message": message}
    return jsonify(response), 200


def make_error(e: Exception):
    """Create a JSON error response."""

    traceback.print_exc()

    exc_type, exc_value, _ = sys.exc_info()
    error_type = exc_type.__name__ if exc_type is not None else type(e).__name__
    error_value = str(exc_value) if exc_value is not None else str(e)

    return jsonify({"success": False, "message": f"{error_type}: {error_value}"}), 200
