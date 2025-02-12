from flask import jsonify


def make_response(success, data=None, message=""):
    """Create a JSON response."""
    response = {"success": success, "data": data if data is not None else {}, "message": message}
    return jsonify(response), 200 if success else 400


def make_error_response(status_code, message):
    """Create a JSON error response."""
    response = {"success": False, "data": {}, "message": message}
    return jsonify(response), status_code


class BaseException(Exception):
    """Base exception class."""

    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code


class ParameterException(BaseException):
    """Exception for invalid parameters."""

    def __init__(self, message="Invalid parameter"):
        super().__init__(message, 400)


class ServiceException(BaseException):
    """Exception for service errors."""

    def __init__(self, message="Service error"):
        super().__init__(message, 500)
