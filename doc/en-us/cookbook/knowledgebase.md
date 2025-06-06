# Knowledge Base

The knowledge base in Chat2Graph is divided into two parts for usage: the global knowledge base and the session knowledge base.

+ **Global Knowledge Base**: The global knowledge base stores the foundational knowledge for the entire agent system. Any session can access knowledge from the global knowledge base.
+ **Session Knowledge Base**: The session knowledge base stores private knowledge related to the current session. It is one-to-one mapped to a session. During the current session, only the corresponding session knowledge base is accessed, and interference from other sessions' knowledge bases is blocked.

The knowledge base module of Chat2Graph is designed to support multi-source and multi-type knowledge base systems. Currently integrated knowledge base systems include:

+ **DB-GPT Vector Knowledge Base**: A vector knowledge base based on ChromaDB. During retrieval, it matches the most relevant document chunks based on vector similarity.
+ **DB-GPT Graph Knowledge Base**: A graph knowledge base based on TuGraph-DB. During retrieval, it matches subgraphs and community summaries related to the query within the knowledge graph.

### 1. System Configuration

Chat2Graph uses the vector knowledge base by default. To specify a different knowledge base type, add the following configuration items to the `.env` file before start:

### 1.1. Vector Knowledge Base

```toml
# Vector Knowledge Base
KNOWLEDGE_STORE_TYPE=VECTOR
```

### 1.2. Graph Knowledge Base

```toml
# Graph Knowledge Base
KNOWLEDGE_STORE_TYPE=GRAPH
# Host of TuGraph-DB
GRAPH_KNOWLEDGE_STORE_HOST=127.0.0.1
# Port of TuGraph-DB
GRAPH_KNOWLEDGE_STORE_PORT=17687
```

## 2. Load Documents

Click the card of the global knowledge base or session knowledge base.

![](../../asset/image/kb-mng.png)

Click the "New" button, select the files to add to the knowledge base.

![](../../asset/image/kb-upload.png)

Configure knowledge base loading configuration(currently supports modification of the `chunk_size` ).

![](../../asset/image/kb-config.png)

After successful file addition, the files will be displayed in the knowledge base management page. Click "Delete" to remove files from the knowledge base.

![](../../asset/image/kb-delete.png)

## 3. Edit Session Knowledge Base

The top-right corner of the session knowledge base card provides functions to edit, clear the knowledge base, and return to the corresponding session.

![](../../asset/image/kb-edit.png)

The "Edit" function allows modification of the knowledge base name and description.

![](../../asset/image/kb-rename.png)

## 4. Q&A on Knowledge Base

After adding knowledge to the knowledge base, Chat2Graph can answer domain-specific questions that the base model cannot handle using the knowledge base's domain knowledge. It also lists references to original documents from the knowledge base. Below is an example response to the question "Introduce Chat2Graph.":

![](../../asset/image/kb-qa.png)
