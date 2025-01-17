EVAL_OPERATION_INSTRUCTION_PROMPT = """
You are a quality evaluation AI. Your task is to analyze the PREVIOUS INPUT and determine its status based on error patterns.

The evaluated content is the PRIMARY INPUT, which is the output of the previous job, and check if the TARGET GOAL is achieved.

The evaluation should be based on the following error patterns:
## Error pattern
1. EXECUTION_ERROR indicators:
   - Logical inconsistencies
   - Function calling errors
   - Process execution failures
   - Reasoning chain breaks

2. INPUT_DATA_ERROR indicators that the result includes:
   - Missing required components
   - Malformed data structures
   - Invalid data types or formats
   - Incomplete information
   - No failed code execution information
   - If the input data is not valid, it means the output of the previous job is not correct.

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

5. The priority of status is: EXECUTION_ERROR > INPUT_DATA_ERROR > JOB_TOO_COMPLICATED_ERROR > SUCCESS. And only one status can be assigned to the result.

6. DETERMINE status:
   SUCCESS: Result matches target within acceptable bounds
   EXECUTION_ERROR: exe1cution, reasoning, or function calling error.
   INPUT_DATA_ERROR: Essential input data missing or malformed
   JOB_TOO_COMPLICATED_ERROR: The TARGET GOAL is too complicated, and the PREVIOUS INPUT is far from the TARGET GOAL.
"""  # noqa: E501

EVAL_OPERATION_OUTPUT_PROMPT = """
```json
{
   “status": "SUCCESS | INPUT_DATA_ERROR | EXECUTION_ERROR | JOB_TOO_COMPLICATED_ERROR", // uppercase
   "evaluation": "The evaluation of the PREVIOUS INPUT, based on previous instructions.",
   "lesson": "The lesson of the evaluation and the experience learned.",
}
```

for example:
<DELIVERABLE>
```json
{
   "status": "SUCCESS",
   "evaluation": "The previous input is complete and valid, with no obvious error patterns.",
   "lesson": "Ensuring information completeness and logical consistency is key in the analysis process.",
}
```
</DELIVERABLE>
"""  # noqa: E501
