TASK_DESCRIPTOR_PROMPT_TEMPLATE = """
===== ACTIONS =====
LLMs need explicit action spaces and valid transitions. This isn't just a list - it's a state machine definition showing valid transitions (-next->) between actions. In addition, not all recommended Actions require the callings of tools/functions, and the names of the actions are not the name of the tools/functions.
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

2. job_id: Uniquely identifies the current job, used to track job status and progress

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

Function Call Rule: For simple arguments, use standard JSON. For complex, multi-line arguments like code, use the Payload Wrapper.

Here are the detailed rules:

1.  **General Format**: All function calls must be wrapped in `<function_call>...</function_call>` tags inside the `<action>` section. You can have multiple `<function_call>` blocks for multiple calls.

2.  **JSON Structure**: The content inside each `<function_call>` must be a valid JSON object with three required keys:
    *   `"name"`: The name of the function to call (string).
    *   `"call_objective"`: A brief description of why you are calling this function (string).
    *   `"args"`: An object containing all arguments for the function. If no arguments are needed, use an empty object `{{}}`.

3.  **Handling Simple Arguments**: For standard data types like short strings, numbers, booleans, or simple nested objects/arrays, use standard JSON format.
    *   Keys and strings must be in **double quotes** (`"`).
    *   Do not use trailing commas.

4.  **Handling COMPLEX Arguments (e.g., Code, HTML, Markdown) - THE EASY WAY**:
    *   Problem**: Multi-line code or text with special characters is extremely difficult and error-prone to escape correctly in a JSON string.
    *   Solution: Instead of escaping, wrap the raw, unescaped content in a **Payload Wrapper**.
    *   Start Marker: `__PAYLOAD_START__`
    *   **End Marker: `__PAYLOAD_END__`
    *   Simply place the raw content between these markers. The system will handle it automatically.

5.  **Execution Flow**: After you provide the `<action>`, a third party will execute the functions and paste the results in `<function_call_result>...</function_call_result>`. You are NOT permitted to generate mock function results.

Function Calling Examples:

**Example 1: Calling a simple function**
<action>
    <function_call>
    {
        "name": "update_user_profile",
        "call_objective": "Update the user's name and notification settings.",
        "args": {
            "user_id": 123,
            "profile": {
                "name": "Alice",
                "notifications_enabled": true
            }
        }
    }
    </function_call>
// Example 2: Calling a function with a COMPLEX code argument (Recommended Method)
    <function_call>
    {
        "name": "execute_python_code",
        "call_objective": "Define a function to greet a user and then call it.",
        "args": {
            "code": __PAYLOAD_START__
def greet(name):
    # This is a comment inside the code.
    # Notice there are no escape characters needed.
    message = f"Hello, {name}! Welcome."
    print(message)

greet("World")
__PAYLOAD_END__
        }
    }
    </function_call>
    <function_call>
    ... ...
    </function_call>
</action>
"""  # noqa: E501

FUNC_CALLING_JSON_GUIDE = """
===== LLM Guide for Correcting Function Call Errors within `<function_call>` =====

A JSON parsing error occurred. Please review your `<function_call>` content.

**>>> COMMON MISTAKE & SOLUTION FOR CODE ARGUMENTS <<<**

*   **MISTAKE**: the system tried to manually escape a multi-line code block or complex string. This is very difficult and often fails.
    // WRONG AND ERROR-PRONE WAY:
<function_call>
    {
      "name": "execute_python_code",
      "args": {
        "code": "def greet(name):\\n    print(f\\"Hello, {{name}}!\\")"
      }
    }
</function_call>

*  **MISTAKE**:
    // WRONG AND ERROR-PRONE WAY: __PAYLOAD_START__ and __PAYLOAD_END__ is enclosed in a pair of double quotes "".
<function_call>
    {
      "name": "execute_python_code",
      "args": {
        "code": "__PAYLOAD_START__\ndef greet(name):\n    print(f\"Hello, {{name}}!\")\n__PAYLOAD_END__"
      }
    }
    ```
</function_call>

*   **SOLUTION**: Use the Payload Wrapper. It's simpler and always correct. Just wrap your raw code with `__PAYLOAD_START__` and `__PAYLOAD_END__`.

    // CORRECT AND SIMPLE WAY:
<function_call>
    {
      "name": "execute_python_code",
      "call_objective": "To run a simple greeting script.",
      "args": {
        "code": __PAYLOAD_START__
def greet(name):
    print(f"Hello, {{name}}!")
__PAYLOAD_END__
      }
    }
</function_call>

**General JSON Syntax Checklist (For non-payload parts):**

1.  **Keys & Strings**: MUST be in DOUBLE QUOTES (`"`).
    *   Correct: `{ "key": "value" }`
    *   Incorrect: `{ 'key': 'value' }`
2.  **Trailing Commas**: NOT ALLOWED after the last item in an object or array.
    *   Correct: `{ "a": 1, "b": 2 }`
    *   Incorrect: `{ "a": 1, "b": 2, }`
3.  **Data Types**: Values must be a string, number, `true`, `false`, `null`, object `{}` or array `[]`.
4.  **No Comments**: Do not use `//` or `/* */` inside the JSON block.
"""  # noqa: E501
