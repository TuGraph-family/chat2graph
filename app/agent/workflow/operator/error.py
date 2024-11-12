from enum import Enum


class OperatorError(Enum):
    """OperatorError defines the error types that can be raised by an operator."""

    INPUT_DATA_ERROR = "Input_Data_Error"
    EXECUTION_ERROR = "Execution_Error"
    TASK_TOO_COMPLICATED_ERROR = "Task_Too_Complicated_Error"
