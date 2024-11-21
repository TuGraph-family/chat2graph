from abc import ABC
from dataclasses import dataclass
from enum import Enum


class OperatorError(Enum):
    """OperatorError defines the error types that can be raised by an operator."""

    INPUT_DATA_ERROR = "Input_Data_Error"
    EXECUTION_ERROR = "Execution_Error"
    TASK_TOO_COMPLICATED_ERROR = "Task_Too_Complicated_Error"


@dataclass
class MethodLesson(ABC):
    """MethodLesson is a dataclass that represents a lesson learned from a method.

    Attributes:
        id (str): The unique identifier of the lesson.
        methodology (str): The methodology used that led to the error.
        lesson (str): The error info and the lesson learned.
        error_type (OperatorError): The type of error that led to the lesson.
        operator_id (str): The unique identifier of the operator that made the mistake.
        operator_name (str): The name of the operator that made the mistake.
        timestamp (str): The timestamp when the mistake was made.
    """

    id: str
    methodology: str
    lesson: str
    error_type: OperatorError
    operator_id: str
    operator_name: str
    timestamp: str
