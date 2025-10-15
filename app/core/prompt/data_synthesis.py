generate_query_tv_template = """
You are a graph database expert proficient in generating high-quality question-answer (QA) pairs based on graph database content.  

Your task is to generate the specified number of QA pairs according to the provided task description and subgraph information.  

The generated QA pairs should cover as many difficulty levels as possible to ensure data diversity, with both questions and answers strictly based on the provided subgraph data without fabricating facts.  


### Task Difficulty Level Information  
This section describes the definitions and types of tasks for different levels: {task_level_info}  


### Task Statistical Information  
A partial set of question-answer pairs is already available, with their statistical information as follows: {task_statistic_info}  

When generating answers, reference the statistical information to cover different questions as comprehensively as possible.  


### Input Information  
**Task Description**: {task_description}  

**Subgraph Information**: {subgraph}  

**Number of QA Pairs**: {num_pairs}  


### Output Requirements  
- **Uniformity**: Achieve balanced coverage across all query types defined in the task difficulty level definitions. Utilize the task statistical information to identify gaps, prioritize generating QA pairs for types with insufficient counts, and avoid undue concentration on 1-2 types. Ensure a reasonable number of QA pairs for each difficulty level, with uniform distribution of query types within each level.  
- **Diversity of Content and Focus**: Adjust the focus on entities and relationships across different QA pairs to avoid repetition of individual entities/relationships, covering all target query type categories such as "attribute filtering" and "relationship existence verification".  
- **Clarity and Accuracy**: Questions should be clear and unambiguous, specifying entities, relationships, or constraints; answers should be accurate and complete, strictly obtaining results from subgraph data and including necessary detailed information.  
- **Answerability**: Perform a consistency check to ensure that the answers to the generated questions are consistent in both the subgraph and the global context, and filter out subgraph aggregation-based questions.  
  - Unanswerable examples (for reference):
    - List all xxx
    - Get all of A's friends
    - Find all xxxx


### Workflow  
1. Analyze entities and relationships in the subgraph.  
2. Based on the task statistical information of existing tasks, determine the question types to prioritize for generation to achieve task diversity and uniform distribution.  
3. Identify the question types that can be raised for each difficulty level.  
4. Generate diverse questions and their correct answers.  
5. Assign appropriate difficulty "level" and task subtype "task_subtype" to each QA pair.  
6. Verify the diversity of generated questions, and generate more diverse questions if they do not meet the requirements.  
7. Verify the answerability of generated questions and filter out questions that do not meet the conditions.  


```json
[
  {{
    "level": "L1",
    "task_subtype": "subtype1",
    "task": "task1",
    "verifier": "anwser1"
  }},
  {{
    "level": "L3",
    "task_subtype": "subtype2",
    "task": "task2",
    "verifier": "anwser2"
  }}
]
```
"""

generate_non_query_tv_template = ""  # TODO

strategy_indentify_template = """
## Role
You are an expert in determining the types of graph database tasks. You are proficient in accurately judging whether a task belongs to the "read-only", "write-only", or "read-write mixed" type based on the description of the graph database task.

## Goal
Based on the task description related to the graph database provided by the user and the given judgment criteria, accurately determine whether the task belongs to the "read-only", "write-only", or "read-write mixed" type.

## Workflow
1. Carefully study the graph database task description provided by the user.
2. Determine whether the task has an obvious write requirement. If not, conduct an in-depth analysis to check for potential write requirements.
3. Determine whether the task has an obvious read requirement. If not, conduct an in-depth analysis to check for potential read requirements.
4. Based on the comprehensive analysis results of reading and writing, determine whether the task is of the "read-only", "write-only", or "read-write mixed" type.
5. Output the classification result according to the output format requirements.

## Constraints
1. The scope of task analysis is limited to "graph databases".
2. Only output the classification result that meets the format requirements, without additional information.

## Output Format
Only output the classification result, which should be one of {strategy_list}

Example 1:
Task description: "Query all product nodes associated with the 'purchase' edges in the past 30 days and count the sales volume of each category."
Output: query

Example 2:
Task description: "Import new user data from a CSV file, create 'User' nodes and 'registration' edges. Confirm whether the 'User' node type definition already exists in the graph before importing."
Output: non-query

Example 3:
Task description: "Detect duplicate 'product' nodes in the graph, delete redundant nodes and merge their associated edges."
Output: mixed


**Please analyze the following task descriptions:**
## Task Description
{task_desc}
"""


filter_prompt_template = """
### Role  
You are a Synthetic Data Evaluation Expert, specializing in evaluating the quality of synthetic data generated based on a local subgraph from a graph database and filtering out low-quality data.  


### Goals  
1. Evaluate the quality of synthetic data based on evaluation criteria.  
2. Filter out low-quality synthetic data that does not meet the criteria.  
3. Output evaluation results in the specified output format.  


### Skills  
1. Possess the ability to judge the authenticity, relevance, and consistency of synthetic data.  
2. Be familiar with knowledge related to local subgraphs in graph databases.  
3. Able to output data in the required JSON format.  


### Evaluation Criteria  
1. Synthetic data must be evaluated based on the criteria of authenticity, relevance, and consistency:
   - **Authenticity**: Judge whether the answers in the synthetic data are based on content in the subgraph; filter out those that are not.  
   - **Relevance**: Judge whether the synthetic data is relevant to the task description; filter out those that are irrelevant.  
   - **Consistency**: Judge whether the synthetic data is consistent between local and global answers; filter out those that are inconsistent. 
      - For example, "finding all friends of A" is generally inconsistent between local and global contexts; most such cases of "finding all xxx" are incorrect, and other types of inconsistencies require independent judgment of consistency.  
      - For example, "Which accounts have an accountLevel of "Gold" and an accountType of "Corporate Account"?" will have more answers globally than locally, so this type of question also needs to be filtered.
2. Data that does not meet the above criteria must be excluded.  


### Task Description  
{task_desc}  


### Subgraph  
{subgraph}  


### Synthetic Data  
{dataset}  

Field Descriptions
- **task**: A string representing the graph database query task description (e.g., "Query the multi-hop relationships of a node", "Filter nodes with specific properties", etc.).
- **verifier**: A string representing the verification criteria or standard answer for the task (e.g., correct query statement, expected return result, judgment logic, etc.).

### Workflow  
1. Carefully review the task description, subgraphs, and synthesized data.
2. Evaluate each synthesized data item by item according to the evaluation criteria.
3. Determine if it meets the authenticity criteria, and filter if it does not.
4. Determine if it meets the relevance criteria, and filter if it does not.
5. Determine if it meets the consistency criteria, and filter if it does not.
6. Filter if any one of ["all", "List"] appears in the `task` field.
7. Organize the data that meets the criteria according to the specified output format. 


### Output Format  
```json
[
  {{
    "level": "L1",
    "task_subtype": "subtype1",
    "task": "task1",
    "verifier": "anwser1"
  }},
  {{
    "level": "L3",
    "task_subtype": "subtype2",
    "task": "task2",
    "verifier": "anwser2"
  }}
]
```
"""