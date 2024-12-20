JOB_DECOMPOSITION_PROMPT = """
===== Task Scope & LLM Capabilities =====

## Role: Decompose the main TASK into {num_subtasks} subtasks for {num_roles} domain experts

## Given Task:
{task}

## Capabilities: Focus on expert strengths (data processing, code generation, content creation)
## You must complete the task decomposition in one round.

===== Expert Names & Descriptions =====
{role_list}

===== Task Structure & Dependencies =====

## Granularity: Create actionable, distinct subtasks with clear boundaries
## Dependencies: Define logical task flow in Gantt-chart compatible format
## Completion: Specify quantifiable completion criteria for each subtask

===== Task Decomposition =====

A. Context Definition
    Global: Task description, constraints, objectives
    Interface: Input/output formats and structures
    Dependencies: Inter-task data flow and requirements

B. Validation & Standards
    Input(scrachpad): Format, schema, data, resources, validation rules
    Expected Output: Structure, acceptance criteria
    Completion: Measurable success metricss

===== Execution Guidelines =====

## Self-contained: Each subtask includes all necessary information
## Role-neutral: Avoid mentioning specific roles unless in TASK
## Boundary-aware: Stay within original TASK scope

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
