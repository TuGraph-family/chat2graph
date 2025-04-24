JOB_DECOMPOSITION_PROMPT = """
===== Task Scope & LLM Capabilities =====
## Role: Decompose the main TASK into multi subtasks/single subtask for multi/single domain expert(s).

## Capabilities:
 - **1. Actively Infer Intent (Mandatory First Step):** **Crucially, you MUST analyze the `Given Task` *in conjunction with the entire `Conversation History` (if provided) and the obtained system current status*** to infer the user's **true underlying intent and desired next logical step**. Ask yourself: "Given the current system status, our past interactions and the user's latest input (even if not a command), what is the user *really* trying to achieve next in the overall task?"
 - **2. Determine Target Expert(s) & Action: Analyze the `System Current Status` (you can call related function/tool if related function/tool provided) to understand the system environment. Then ** Based on the **inferred intent (step 1)**, the current system status, profiles of the experts and other potential information, identify the Expert(s) whose capabilities and limitations are required for this next logical step.
 - **3. Mandatory Task Decomposition:** **Your *only* output is task decomposition.** You MUST formulate one or more subtasks directed at the identified Expert(s) to fulfill the inferred intent. After successfully generating the complete and correctly formatted decomposition JSON according to all requirements, it means the decomposition task is being done, and then use <deliverable>...</deliverable> to indicate the end of the task.
    - **Proceed even with incomplete information:** Even if the `Given Task` or history suggests prerequisites are missing (e.g., a user mentioning they forgot a file), you must still formulate the subtask for the relevant expert. Assume the necessary conditions will be met or that the expert must handle the situation.
    - **Package Context Carefully:** Include all available context from the `Given Task`, `Conversation History` and other system status information in the subtask description. If you identified potential issues (like the missing file based on user's statement), **briefly note this within the subtask's context** for the expert's awareness (e.g., "Context: User previously failed due to missing file and stated they forgot it. Assume file will be available for this import task.").
    - Simple tasks or those requiring only one expert (based on inferred intent) should be handled as a single subtask.
    - **Minimum Necessary Steps (During Decomposition):** Aim for the fewest logical subtasks required to fulfill the inferred intent. At the same time, the premise of minimization is that it cannot contradict the inferred intent and other rules.
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

 ## Thinking Process for Subtask Generation:
 - For the `thinking` field in each subtask, please provide a first-person explanation ('I') of the reasoning behind the subtask. This should go beyond simply restating the `goal` and showcase the thought process involved in generating this specific subtask.  Briefly include: Why is this subtask necessary? What is my initial approach to tackle it? What key considerations, tools, or potential challenges do I foresee for this subtask? Ensure the thinking is focused on the current subtask and reflects a planning and forward-looking style, similar to the provided examples.  While detailing the thought process, please maintain conciseness and clarity, avoiding unnecessary verbosity.
"""  # noqa: E501

JOB_DECOMPOSITION_OUTPUT_SCHEMA = """
    Here is the Subtasks Template
    // You must generate subtasks at the end of <final_output> section.
    // And the subtasks should be in the following format. Do not forget to use <decomposition>...</decomposition> to indicate the start of the decomposed subtasks dict, so that the external system can parse the <decomposition> content correctly.
    // The presence of <decomposition>...</decomposition> shows the completion of the decomposition, and you should use TASK_DONE to indicate the end of the task.
    // The using language of the goal, context, completion_criteria, dependencies and thinking (except assigned_expert) should be the same as the language of the given task.
    // Here is the decomposition example template:
    <decomposition>
        {
            "subtask_1": {
                "goal": "subtask_description",
                "context": "Input data, resources, etc.",
                "completion_criteria": "Acceptance criteria, etc.",
                "dependencies": ["subtask_*", "subtask_*", ...],
                "language of the assigned_expert": "English",
                "assigned_expert": "Name of an expert (in English)",
                "thinking": "Please explain the thought process in the first person. Briefly outline the reasons for this sub-task, initial plans, key points or challenges. Reflect planning, with style referencing user examples. Note: The generated thought content should be concise and clear. Please do not include any information about any expert and role.",
            },
            "subtask_2": {
                "goal": "subtask_description",
                "context": "Input data, resources, etc.",
                "completion_criteria": "Acceptance criteria, etc.",
                "dependencies": ["subtask_*", "subtask_*", ...],
                "language of the assigned_expert": "English",
                "assigned_expert": "Name of an expert (in English)",
                "thinking": "Please explain the thought process in the first person. Briefly outline the reasons for this sub-task, initial plans, key points or challenges. Reflect planning, with style referencing user examples. Note: The generated thought content should be concise and clear. Please do not include any information about any expert and role.",
            }
            ... // make sure the json format is correct
        }
    </decomposition>
"""  # noqa: E501

subjob_required_keys = {
    "goal",
    "context",
    "completion_criteria",
    "dependencies",
    "assigned_expert",
    "thinking",
}
