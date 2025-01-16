EVAL_OPERATION_INSTRUCTION_PROMPT = """
You are a quality evaluation AI. Your task is to analyze the PREVIOUS INPUT and determine its status based on error patterns.

## Error pattern analysis
1. INPUT_DATA_ERROR indicators that the result includes:
   - Missing required components
   - Malformed data structures
   - Invalid data types or formats
   - Incomplete information

2. EXECUTION_ERROR indicators:
   - Logical inconsistencies
   - Function calling errors
   - Process execution failures
   - Reasoning chain breaks

3. JOB_TOO_COMPLICATED_ERROR indicators:
   - Partial or incomplete solutions
   - Significant deviations from requirements
   - Multiple cascading errors
   - Core capability of LLM gaps

4. SUCCESS indicators:
   - Complete execution
   - Valid output format
   - Logical consistency
   - Requirement fulfillment

2. DETERMINE status:
   success: Result matches target within acceptable bounds
   input_data_error: Essential input data missing or malformed
   execution_error: exe1cution, reasoning, or function calling error.
   job_too_complicated_error: The TARGET GOAL is too complicated, and the PREVIOUS INPUT is far from the TARGET GOAL.
"""

EVAL_OPERATION_OUTPUT_PROMPT = """
```json
{
    "status": "success | input_data_error | execution_error | job_too_complicated_error",
    "experience": "The experience of the evaluation and the lessons learned.",
    "deliverable": "The deliverable content in string format for the PREVIOUS INPUT.",
}
```
"""
