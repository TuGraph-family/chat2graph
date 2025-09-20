synthesis_prompt_template = """
**Instructions:**

You are tasked with generating a set of task-verifier pairs based on the following information:
- **Task Description (T):** 
    "{task_description}"
- **Subgraph (G):**  
    "{subgraph}"
Please generate **{num_pairs}** question-answer pairs that are:
1. **Relevant:** Directly related to the task description TT and the entities and relationships present in the subgraph GG.
2. **Varied:** Covering different types of questions, such as:
    - Entity identification (e.g., "Who is xiaoming?")
    - Attribute retrieval (e.g., "What is xiaoming's birthday?")
    - Relationship queries (e.g., "What is the relationship between xiaoming and xiaohong?")
    - Temporal or sequential questions (e.g., "What happened before/after Bigbang?")
    - Single-Hop Relationship Queries: Questions that require understanding a direct relationship between two entities.
        (e.g., ""What is the capital of France?"")
    - Multi-Hop Reasoning: Questions that necessitate traversing multiple relationships to derive an answer. 
        (e.g., "Which companies have employees who worked at both Company X and Company Y?")
    - Conditional or Contextual Queries: Questions that depend on specific conditions or contexts.
        (e.g., "Which products are recommended for users who liked Product A?")
3. **Clear and Concise:** Each question should be straightforward, and the answer should be precise and based on the information in GG.

**Format:**
Provide the output as a JSON array of objects, each containing:
```json
[
  {{
    "task": "task_descption1",
    "verifier": "task_verifier_1"
  }},
  {{
    "task": "task_descption1",
    "verifier": "task_verifier_2"
  }},
  ...
]
```

Please only output the array without anything else.

**Example:**
Given the task description:
"Identify the employees working in 'Company A' and their respective roles."

And the subgraph:
```json
{{
    "nodes": [
        {{"id": 1, "labels": ["Person"], "properties": {{"name": "Alice", "role": "Engineer"}}}},
        {{"id": 2, "labels": ["Person"], "properties": {{"name": "Bob", "role": "Manager"}}}},
        {{"id": 3, "labels": ["Company"], "properties": {{"name": "Company A"}}}}
    ],
    "relationships": [
        {{"id": 101, "type": "WORKS_AT", "start_node_id": 1, "end_node_id": 3, "properties": {{}}}},
        {{"id": 102, "type": "WORKS_AT", "start_node_id": 2, "end_node_id": 3, "properties": {{}}}}
    ]
}}
```

The generated QA pairs might include:
```json
[
  {{
    "task": "Who works at Company A?",
    "verifier": "Alice and Bob work at Company A."
  }},
  {{
    "task": "What is Alice's role?",
    "verifier": "Alice is an Engineer."
  }},
  {{
    "task": "What is Bob's role?",
    "verifier": "Bob is a Manager."
  }}
]
"""


