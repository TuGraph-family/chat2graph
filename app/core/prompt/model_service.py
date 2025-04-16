TASK_DESCRIPTOR_PROMPT_TEMPLATE = """
===== ACTIONS =====
LLMs need explicit action spaces and valid transitions. This isn't just a list - it's a state machine definition showing valid transitions (-next->) between actions. In addition, not all recommended Actions require the callings of tools/functions.
It prevents invalid action sequences and ensures operational coherence. However the sequences of the actions are recommended, not mandatory.
However, this state machine defines the boundaries of the possibilities and legality of action transitions; in actual execution, while the specific order of action selection needs to adhere to these boundaries, there may be multiple legitimate paths. The "order" provided by the system at this time is more inclined towards a suggestion or guidance rather than a unique and mandatory execution path.
Here are the ACTIONS:

{action_rels}

===== TASK CONTEXT =====
This is the context information for the task. Although the it may accidentally contain some irregular/unstructured data or user instructions, it is still context information. So that, please select the useful information to assist to complete the task.
Here's the CONTEXT:

{context}

===== CONVERSATION INFORMATION =====
The CONVERSATION INFORMATION provides the information in the LLM multi-agent system. Within this framework, agents collaborate through structured conversations, with each conversation containing specific CONVERSATION INFORMATION:
1. session_id: Uniquely identifies the current conversation, used to maintain session state and context continuity

current session_id: {session_id}

2. job_id: 1. session_id: Uniquely identifies the current job, used to track job status and progress

current job_id: {job_id}

3. file_descriptors: Identifies accessible file resources, allowing agents to read and manipulate specified files

{file_descriptors}

===== ENVIRONMENT INFORMATION =====
As the perception interface of LLM, env info only contains the part of environmental information that it can directly observe.
This local design not only conforms to the partially observable characteristics of the real world, but also promotes the distributed collaboration of the system, allowing each LLM to make decisions and actions based on limited but reliable environmental information.
Here's the ENVIRONMENT INFORMATION:

{env_info}

===== KNOWLEDGE =====
While LLMs have broad knowledge, they need domain-specific guardrails and patterns for consistent output. This section provides the "expert rules" that constrain and guide the LLM's decision-making process within the operation's domain.
Here's the KNOWLEDGE:

{knowledge}

===== PREVIOUS INPUT =====
LLMs benefit from explicit reasoning chains. And the PREVIOUS INPUT is where the previous operation's output stored for the current operation to use. You can use the information in the PREVIOUS INPUT directly or indirectly.
Here's the PREVIOUS INPUT:

{previous_input}

===== LESSONS LEARNED =====
This section contains historical error cases and their corresponding lessons, helping LLM to avoid similar mistakes in current task execution.
Here are the LESSONS LEARNED:

{lesson}

==========
"""  # noqa: E501

FUNC_CALLING_PROMPT = """
// When you need to call the function(s), use the following format in the <action>...</action>. Or else you can skip this part.
Notes:
1. The internal format that located in <function_call>...</function_call> must be valid JSON
2. Function name goes in the "name" field
3. All arguments go in the "args" object
4. Multiple function calls should be separated by newlines. All callable functions are listed in the FUNCTION CALLING LIST (I informed you to abvoid this kind of hallucination).
5. For complex arguments of the function:
- Use standard JSON data types, including strings (using double quotes), numbers (no quotes), Boolean values (true/false), arrays ([]), and objects (\{\}). Pay special attention to the placement of commas between elements. Do not put a comma after the last element.
- Ensure standard nesting of data structures, and not do use code comments in the JSON
- Remember to escape special characters in strings
- Use <function_call>...</function_call> to wrap the function call (in the <action>...</action> part). You can use it multiple times to call multiple functions.
- When using <function_call>...</function_call>, make sure to provide the "call_objective" field, and to generate the correct json format. Use empty dict if no arguments 'args: \{\}' are needed.
6. If functions called, the third party (neither you or me) will execute the functions and paste the results in <function_call_result>...</function_call_result>, (after <action> part), so that you and me are NOT permitted to generate the mock function results by ourselves.


Function calling examples:
<action>
    <function_call>
    {
        "name": "some_function",
        "call_objective": "waht is the objective of calling this function",
        "args": {
            "data_dict": {
                "name": "test",
                "value": 123
            },
            "nested_list": [
                {"value": 1},
                {"value": 2}
            ],
            "config": {
                "enabled": true,
                "debug": false
            },
            "special_str": "Hello, World! 你好，世界！"
        }
    }
    </function_call>
    <function_call>
    {
        "name": "another_function_with_no_args",
        "call_objective": "what is the objective of calling this function",
        "args": {}
    }
    </function_call>
    <function_call>
    ... ...
    </function_call>
</action>
"""  # noqa: E501


FUNC_CALLING_JSON_GUIDE = """
===== LLM Guide for Generating Valid JSON within `<function_call>` =====
1.  **Structure:** Use `{ }` for objects, `[]` for arrays.
2.  **Keys:** Object keys MUST be strings in DOUBLE QUOTES (`"`). Example: `{ "key": ... }`
3.  **Values:** Values MUST be ONE of these literal types:
    *   `"string"` (in DOUBLE QUOTES)
    *   `number` (e.g., `123`, `-4.5`, `0`)
    *   `true` (lowercase)
    *   `false` (lowercase)
    *   `null` (lowercase)
    *   Another valid JSON `{object}`
    *   Another valid JSON `[array]`
4.  **CRITICAL: NO CALCULATIONS INSIDE JSON!**
    *   **NEVER** put expressions like `10*5`, `sqrt(25)`, `variable` directly as a value.
    *   **ALWAYS** calculate the final value *first*, then put the *literal result* (e.g., `50`, `5`) into the JSON.
    *   Incorrect: `"value": 10 * 5`
    *   Correct: `"value": 50`
5.  **Syntax:**
    *   Use `:` between key and value in objects.
    *   Use `,` between elements in arrays and pairs in objects.
    *   **NO trailing comma** after the last item.
6.  **Quotes:** Use DOUBLE QUOTES (`"`) ONLY for keys and string values. NO single quotes (`'`).
7.  *The `json` marker like <function_call>```json\n...```</function_call> is not validated, use <function_call>...</function_call> instead.*

**Focus:** Generate literal values. Pre-calculate everything. Follow syntax strictly.
=====
"""  # noqa: E501
