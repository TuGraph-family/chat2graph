TASK_DESCRIPTOR_PROMPT_TEMPLATE = """
===== CONTEXT =====
{context}

===== ENVIRONMENT INFORMATION =====
As the perception interface of LLM, env info only contains the part of environmental information that it can directly observe.
This local design not only conforms to the partially observable characteristics of the real world, but also promotes the distributed collaboration of the system, allowing each LLM to make decisions and actions based on limited but reliable environmental information.
Here's the ENVIRONMENT INFORMATION:

{env_info}

===== KNOWLEDGE =====
While LLMs have broad knowledge, they need domain-specific guardrails and patterns for consistent output. This section provides the "expert rules" that constrain and guide the LLM's decision-making process within the operation's domain.
Here's the KNOWLEDGE:

{knowledge}

===== ACTIONS =====
LLMs need explicit action spaces and valid transitions. This isn't just a list - it's a state machine definition showing valid transitions (-next->) between actions.
It prevents invalid action sequences and ensures operational coherence. However the sequences of the actions are recommended, not mandatory.
Here are the ACTIONS:

{action_rels}

===== PREVIOUS INPUT =====
LLMs benefit from explicit reasoning chains. And the PREVIOUS INPUT is where the previous operation's output stored for the current operation to use. You can use the information in the PREVIOUS INPUT directly or indirectly.
Here's the PREVIOUS INPUT:

{scratchpad}

==========
"""

FUNC_CALLING_PROMPT = """
    // When you need to call the function(s), use the following format in the <Feedback>. Or else you can skip this part.
    Notes:
    1. The format must be valid JSON
    2. Function name goes in the "name" field
    3. All arguments go in the "args" object
    4. Multiple function calls should be separated by newlines
    5. For complex arguments:
    - Use proper JSON data types (strings, numbers, booleans, arrays, objects)
    - Ensure proper nesting of data structures
    - Remember to escape special characters in strings
    - Use <function_call>...</function_call> to wrap the function call (in the <Action> part). You can use it multiple times to call multiple functions.
    - When using <function_call>...</function_call>, make sure to provide the "call_objective" field.
    6. If functions called, the program will execute the functions and paste the results at the end of <Feedback> part.

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
"""
