JOB_DECOMPOSITION_PROMPT = """
===== Task Scope & LLM Capabilities =====

## Role: Decompose the main TASK into multi subtasks/single subtask for multi/single domain expert(s).

## Given Task:
{task}

## Capabilities: Focus on expert strengths, and provide the contextual information for each of them.
## Self-contained: Each subtask includes all necessary information
## Role-neutral: Avoid mentioning specific roles unless in TASK
## Boundary-aware: Stay the subtasks within original TASK scope
## You must complete the task decomposition in one round.

===== Expert Names & Descriptions =====
{role_list}

===== Task Structure & Dependencies =====

## Granularity: Create actionable, distinct subtasks with clear boundaries
## Context: Provied every necessary information in details, and state in verbose the expected input from the previous task & the expected input to the next task, so that the expert can aquire the contextual information and, can deliver it to the next task with the current task result & information
## Dependencies: Define logical task flow in Gantt-chart compatible format
## Completion Criteria: Specify quantifiable completion criteria for each subtask

"""

JOB_DECOMPOSITION_OUTPUT_SCHEMA = """
Here is the Subtasks Template
// You must generate subtasks at the end of <DELIVERABLE> section.
// And the subtasks should be in the following json format.
// Must use ```json``` to mark the beginning of the json content.
```json
{
    "specific_task_id": 
    {
        "goal": "subtask_description",
        "context": "Input data, resources, etc.",
        "completion_criteria": "Acceptance Criteria, etc.",
        "dependencies": ["specific_task_id_*", "specific_task_id_*", ...],
        "assigned_expert": "Name of an expert (in English.)",
    }
    "specific_task_id":
    {
        "goal": "subtask_description",
        "context": "Input data, resources, etc.",
        "completion_criteria": "Acceptance Criteria, etc.",
        "dependencies": ["specific_task_id_*", "specific_task_id_*", ...],
        "language of the assigned_expert": "Engilish",
        "assigned_expert": "Name of an expert (in English.)",
    }
    ... // make sure the json format is correct
}
```
"""
