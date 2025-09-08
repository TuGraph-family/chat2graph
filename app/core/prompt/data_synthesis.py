generate_query_tv_template = """
You are an expert in graph databases, proficient in generating high-quality question–answer pairs (QA pairs) based on graph data structures.  
Your task is to generate the specified number of QA pairs according to the provided task description and sub-graph information.  
These QA pairs must cover as many difficulty levels as possible and use a **variety of query types**, while ensuring that both questions and answers are strictly based on the provided sub-graph data (no fabricated information).

### Task Difficulty Levels

{task_level_info}

### Task Statistic Info
There are already some question-answer pairs, and its statistics are as follows:

{task_statistic_info}

### Generation Requirements

1. **Input Information**  
**Task description**: 
{task_description}  
   
**Sub-graph information**: 
{subgraph}  
   
**Number of QA pairs**: {num_pairs}  

2. **Output Requirements**  
**Dual Foundation Alignment**:  
  - All questions and answers must be strictly based on two core references:  
    **Task Difficulty Levels**: Follow the subtask categories, logic, and difficulty definitions (L1–L3) specified in the task framework (e.g., L1 for single-hop queries, L2 for multi-hop reasoning, L3 for basic algorithm applications).  
    **Task Statistic Info**: Refer to the distribution of existing QA pairs to guide new QA generation—prioritize supplementing underrepresented types rather than repeating overrepresented ones.  

**Uniform Distribution of QA Pairs**:  
  - Aim for balanced coverage across all query types defined in Task Difficulty Levels. Use Task Statistic Info to identify gaps (e.g., if "Basic Path Analysis" has far fewer QAs than "Simple Attribute Filtering"), and prioritize generating QAs for undercounted types to avoid over-concentration on 1–2 types.  
  - Ensure each difficulty level (L1-L3) has a reasonable number of QAs, and the query type distribution within each level is also uniform.  

**Diversity in Content & Focus**:  
  - Vary the focus of entities and relationships across QAs to avoid single-entity/relationship repetition.  
  - Cover all target query type categories as defined, including but not limited to: `attribute filtering`, `relationship existence verification`, `multi-hop pattern matching`, `statistical aggregation`, `ranking/top-K`, `path analysis (shortest/longest)`, `community detection`, `centrality/influence calculation`.  

**Clarity & Accuracy**:  
  - Questions must be clear and specific: Clearly specify entities, relationships, or constraints.  
  - Answers must be accurate and complete: Derive results strictly from sub-graph data, and include necessary details .  

**Explicit Level Labeling**: Each QA pair must clearly mark its difficulty level (L1/L2/L3) in the `"level"` field and task subtype(eg. Entity Attribute and Label Query) in the `"task_subtype"` field, ensuring consistency with the classification in Task Difficulty Levels.

3. **Workflow for You**  
   - Analyse the entities and relationships in the sub-graph.  
   - Determine for each difficulty level (L1-L3) what types of questions can be asked.
   - Based on the Task Statistic Info of the existing tasks, decide which task subtypes to generate for more diverse and evenly distributed tasks.
   - Generate diverse questions accordingly and their correct answers.  
   - Assign the appropriate difficulty `"level"` and task subtype `"task_subtype"` to each QA pair.

4. **Output Format**  
   Output **only** a JSON list. Each element must contain four fields: `"level"` (L1/L2/L3/L4), `"task_subtype"` (specific subtask type), `"task"` (question), and `"verifier"` (answer).  
   Example:
   ```json
   [
     {{
       "level": "L1",
       "task_subtype" : sbutype1
       "task": "Question description 1",
       "verifier": "Answer 1"
     }},
     {{
       "level": "L3",
       "task_subtype" : subtype2, 
       "task": "Question description 2",
       "verifier": "Answer 2"
     }}
   ]
  ```
"""
generate_query_tv_template_old = """
You are an expert in graph databases, proficient in generating high-quality question-answer pairs (QA pairs) based on graph data structures. Please generate the specified number of QA pairs according to the provided task description and sub-graph information. These QA pairs should cover as many difficulty levels as possible, while ensuring that both questions and answers are based on the provided sub-graph data.

### Definition of Task Difficulty Levels

#### L1: Simple Query Tasks
- Single-hop relationship queries and simple attribute filtering, generally 0-1 hop, without reasoning.
- Includes: Single-node attribute queries, single-edge relationship existence checks, index query by ID.
- Typical examples:
 - Query the registration time and membership level of a certain user.
 - Find entities with the node label "User" and the city as "Beijing".
 - Verify whether user u1001 follows user u2002.
 - Filter product nodes with a price > 1000 yuan.
 - Count the total number of nodes of the "Product" type in the graph.

#### L2: Simple Multi-hop Queries
- Multi-hop path queries and pattern matching, which require integrating information from multiple entities and include simple filtering.
- Typical examples:
 - Query the second-degree friends of user u100.
 - Query "the brands of products purchased by user u1001" (user → purchase → product → belong to → brand).
 - Count the number of "direct friends of user u1001 whose age < 30 years old".
 - Query all interaction relationships (such as likes, collections, comments) of user u1001 with "content c5001".

#### L3: Complex Association Queries
- Involve long-path queries of ≥ 4 hops or sub-graph level analysis, require multi-attribute cross-type filtering; may involve simple graph algorithms.
- Typical examples:
 - Query the names of suppliers in the path "user u1001 → purchase → product → belong to → brand → cooperate with → supplier → located in", where "the supplier is located in Shanghai and the product price > 500".
 - Analyze "the top 3 brands with the highest sales volume and their average prices among the electronic products purchased by users in Beijing".
 - Find the shortest path from user A to user B.
 - Identify interest groups in an e-commerce platform.
 - Identify key dissemination nodes in a social network.

#### L4: Algorithm-based Reasoning Queries
- Complex reasoning based on graph algorithms, dynamic path analysis, requiring in-depth logical reasoning.
- Typical examples:
 - Query the top 5 core users with the highest influence in the social sub-graph where user u1001 is located.
 - Query the longest path containing ≥ 5 nodes among all possible paths from the raw material supplier to the end-user of product p7001.
 - Identify the fraud-risk community where user u1001 is located and query the number of transaction records of all users in this community.
 - Detect whether there is a money-laundering cycle in the financial transaction graph.
 - Predict the cascading impact after the failure of a certain node in the supply chain.

### Generation Requirements

1. Generate QA pairs based on the following information:
  - Task description: {task_description}
  - Sub-graph information: {subgraph}
  - Number of pairs to generate: {num_pairs} QA pairs

2. The generated QA pairs should meet the following requirements:
  - Questions and answers must be based on the provided sub-graph data, and no information that does not exist in the sub-graph can be fabricated.
  - Cover as many difficulty levels (L1-L4) as possible, but it is not mandatory to generate questions for all levels. If the sub-graph does not support tasks of a certain level, that level can be skipped.
  - Ensure diversity: Cover different entities, relationships, attributes, and query types (attribute, relationship, path, statistics, algorithm-based reasoning). Avoid repeated or highly similar questions.
  - Questions should be clear and specific, and answers should be accurate and complete.
  - Output the results only in JSON list format, where each element contains three fields: "task", "verifier", and "level". Among them, "level" can only be one of L1, L2, L3, L4.

### Workflow
1. Analyze the entities, relationships, etc. in the sub-graph based on the sub-graph information, and pay attention to the association relationships between entities.
2. Analyze in turn whether questions of levels L1-L4 can be raised based on the sub-graph.
3. Based on the above analysis, raise several questions.
4. For each question, conduct in-depth analysis and generate its corresponding answer.
5. For each question, conduct in-depth analysis and generate its corresponding difficulty level.

### Output Format:
Please output the results in JSON list format, where each element contains two fields: "task" (question description) and "verifier" (answer). The specific format is as follows:
```json
[
  {{
    "task": "Question description 1",
    "level": "L1",
    "verifier": "Answer 1"
  }},
  {{
    "task": "Question description 2",
    "level": "L2",
    "verifier": "Answer 2"
  }},
  ...
]
```
"""

generate_non_query_tv_template = "" # TODO

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