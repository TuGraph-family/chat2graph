from typing import Any, Optional

from flask import jsonify


class ApiException(Exception):
    """Base exception class."""

    def __init__(self, message: str, status_code: int = 400):
        self.message: str = message
        self.status_code: int = status_code


def make_response(success: bool, data: Optional[Any] = None, message: str = "") -> Any:
    """Create a JSON response."""
    response = {"success": success, "data": data if data is not None else {}, "message": message}
    return jsonify(response), 200 if success else 400


def make_error_response(status_code, message):
    """Create a JSON error response."""
    response = {"success": False, "data": {}, "message": message}
    return jsonify(response), status_code
