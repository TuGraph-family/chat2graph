from typing import Any, Dict

from flask import jsonify


class BaseException(Exception):
    """Base exception class."""

    def __init__(self, message: str, status_code: int = 400):
        self.message: str = message
        self.status_code: int = status_code


class ParameterException(BaseException):
    """Exception for invalid parameters."""

    def __init__(self, message="Invalid parameter"):
        super().__init__(message, 400)


class ServiceException(BaseException):
    """Exception for service errors."""

    def __init__(self, message="Service error"):
        super().__init__(message, 500)


def make_response(success, data=None, message=""):
    """Create a JSON response."""
    response = {"success": success, "data": data if data is not None else {}, "message": message}
    return jsonify(response), 200 if success else 400


def make_error_response(status_code, message):
    """Create a JSON error response."""
    response = {"success": False, "data": {}, "message": message}
    return jsonify(response), status_code


def validate_params(params: Dict[str, Any], rules: Dict[str, type]):
    """Validate parameters based on the given rules.

    Args:
        params (Dict[str, Any]): Dictionary of parameters to validate
        rules (Dict[str, type]): Dictionary of parameter names and their expected types
    """
    for param_name, param_value in params.items():
        if param_name in rules:
            expected_type = rules[param_name]
            if param_value is None:
                continue  # allow None values for optional parameters
            if not isinstance(param_value, expected_type):
                raise ParameterException(f"{param_name} must be of type {expected_type.__name__}")
