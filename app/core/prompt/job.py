JOB_DECOMPOSITION_PROMPT = """
===== Task Scope & LLM Capabilities =====
## Role: Decompose the main TASK into multi subtasks/single subtask for multi/single domain expert(s).

## Capabilities:
 - Focus on expert strengths, and provide the contextual information for each of them.
 - **First, evaluate if the `Given Task` is simple enough to be handled entirely by a single expert without decomposition.** Simple informational requests (e.g., "introduce X", "Define Y", "Compare A and B", "Help me correct the grammar syntax errors") often require only the one or two experts.
 - Critically evaluate the `Given Task` to determine the *minimum necessary* steps and experts required to make progress. **If decomposition *is* truly needed, aim for the fewest logical steps.** Avoid creating multiple subtasks if one expert can fulfill the entire `Given Task`.
 - **Only assign subtasks to experts whose capabilities, as strictly defined in their profiles, are directly and immediately needed.** Do not assign database modeling, importation, querying, or analysis tasks if the `Given Task` is purely informational and doesn't require interaction with a specific, data-filled graph instance.
## Self-contained: Each subtask includes all necessary information.
## Role-neutral: Avoid mentioning specific roles unless in TASK.
## Boundary-aware: Stay the subtasks within original TASK scope.
## You must complete the task decomposition in one round. **If the task requires only one step/expert, present it as a single subtask.**

==== Given Task ====
{task}

===== Expert Names & Descriptions =====
{role_list}

===== Task Structure & Dependencies =====
## Granularity: Create actionable, distinct subtasks with clear boundaries **only if the task genuinely requires multiple steps involving different expert capabilities.** **For simple tasks solvable by one expert, create only ONE subtask encompassing the entire `Given Task`, informed by the conversation history.**

## Goal Formulation (Influenced by Conversation History):
 - The subtask `goal` **MUST** be precisely phrased to reflect the user's latest request *as understood through the lens of the `Conversation History`*.

## Context (Incorporating Conversation History):
 - Provide all necessary details for the expert. **This field MUST include**:
    1.  A concise summary of the relevant `Conversation History`: Briefly state what was asked/answered previously.
    2.  The user's feedback/pivot: Mention if the user expressed dissatisfaction, asked for clarification, corrected the direction, or narrowed the scope (e.g., "User found the previous answer too general," "User specifically asked to ignore X and focus on Y," "User corrected the previous assumption about Z", "User want to move on to the next task based on the previous efforts.")
    3.  How the Conversation History shapes the current task: Explicitly state how points 1, 2, etc lead to the specific requirements of the current `goal`.
 - State expected inputs (if any beyond the context itself) and the nature of the expected output.

## Dependencies:
- Define logical subtasks flow **only if multiple subtasks are generated**. Simple, single-subtask decompositions have no dependencies.

## Completion Criteria (Reflecting Conversation History):
 - Specify clear, measurable, or verifiable criteria for successful completion.
 - These criteria MUST directly address the specific need or correction highlighted by the `Conversation History` and the refined `goal`.**
 - Example: If the history shows the user lacked syntax details, a criterion MUST be "The output provides concrete syntax examples for operations A, B, and C." If the history shows dissatisfaction with generality, a criterion MUST be "The explanation avoids overly broad statements and focuses on the specific aspect requested."
"""  # noqa: E501

JOB_DECOMPOSITION_OUTPUT_SCHEMA = """
Here is the Subtasks Template
// You must generate subtasks at the end of <deliverable> section.
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
