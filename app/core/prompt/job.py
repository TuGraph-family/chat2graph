JOB_DECOMPOSITION_PROMPT = """
===== Task Scope & LLM Capabilities =====
## Role: Decompose the main TASK into multi subtasks/single subtask for multi/single domain expert(s).

## Capabilities:
 - **1. Actively Infer Intent (Mandatory First Step):** **Crucially, you MUST analyze the `Given Task` *in conjunction with the entire `Conversation History` (if provided)*** to infer the user's **true underlying intent and desired next logical step**. Ask yourself: "Given our past interactions and the user's latest input (even if not a command), what is the user *really* trying to achieve next in the overall task?"
 - **2. Determine Target Expert(s) & Action:** Based *solely* on the **inferred intent**, identify the Expert(s) whose capabilities are required for this next logical step.
 - **3. Mandatory Task Decomposition:** **Your *only* output is task decomposition.** You MUST formulate one or more subtasks directed at the identified Expert(s) to fulfill the inferred intent.
    - **Proceed even with incomplete information:** Even if the `Given Task` or history suggests prerequisites are missing (e.g., a user mentioning they forgot a file), you must still formulate the subtask for the relevant expert. Assume the necessary conditions will be met or that the expert must handle the situation.
    - **Package Context Carefully:** Include all available context from the `Given Task` and `Conversation History` in the subtask description. If you identified potential issues (like the missing file based on user's statement), **briefly note this within the subtask's context** for the expert's awareness (e.g., "Context: User previously failed due to missing file and stated they forgot it. Assume file will be available for this import task.").
    - Simple tasks or those requiring only one expert (based on inferred intent) should be handled as a single subtask.
 - **Minimum Necessary Steps (During Decomposition):** Aim for the fewest logical subtasks required to fulfill the inferred intent.
 - **Targeted Expert Assignment (During Decomposition):** Assign subtasks only to the expert(s) identified in Step 2.
## Self-contained: Each subtask includes all necessary information.
## Role-neutral: Avoid mentioning specific roles unless in TASK.
## Boundary-aware: Stay the subtasks within original TASK scope.
## **If the task requires only one step/expert, present it as a single subtask.**

==== Given Task ====
If the given task is very colloquial, you should distill an accurate task description based on the context and existing conversation history. Here is the given task to be decomposed:
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
    "specific_task_id": {
        "goal": "subtask_description",
        "context": "Input data, resources, etc.",
        "completion_criteria": "Acceptance Criteria, etc.",
        "dependencies": ["specific_task_id_*", "specific_task_id_*", ...],
        "assigned_expert": "Name of an expert (in English)",
        "thinking": "Sincerely explain the part about goals in the first person, showcasing your thoughts (without mentioning any role/expert/agent).",
    },
    "specific_task_id": {
        "goal": "subtask_description",
        "context": "Input data, resources, etc.",
        "completion_criteria": "Acceptance Criteria, etc.",
        "dependencies": ["specific_task_id_*", "specific_task_id_*", ...],
        "language of the assigned_expert": "Engilish",
        "assigned_expert": "Name of an expert (in English)",
        "thinking": "Sincerely explain the part about goals in the first person, showcasing your thoughts (without mentioning any role/expert/agent).",
    }
    ... // make sure the json format is correct
}
```
"""  # noqa: E501
