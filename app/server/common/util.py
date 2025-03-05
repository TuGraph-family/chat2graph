from typing import Any, Dict, Optional

from flask import jsonify


class ApiException(Exception):
    """Base exception class."""

    def __init__(self, message: str, status_code: int = 400):
        self.message: str = message
        self.status_code: int = status_code


class ParameterException(ApiException):
    """Exception for invalid parameters."""

    def __init__(self, message="Invalid parameter"):
        super().__init__(message, 400)


class ServiceException(ApiException):
    """Exception for service errors."""

    def __init__(self, message="Service error"):
        super().__init__(message, 500)


def make_response(success: bool, data: Optional[Any] = None, message: str = ""):
    """Create a JSON response."""
    response = {"success": success, "data": data if data is not None else {}, "message": message}
    return jsonify(response), 200 if success else 400


def make_error_response(status_code, message):
    """Create a JSON error response."""
    response = {"success": False, "data": {}, "message": message}
    return jsonify(response), status_code
