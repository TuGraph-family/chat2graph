🌐️ English | [中文](doc/README-cn.md)

<p align="center">
  <img src="doc/img/head.png" width=800/>
</p>


[![Star](https://shields.io/github/stars/tugraph-family/chat2graph?logo=startrek&label=Star&color=yellow)](https://github.com/TuGraph-family/chat2graph/stargazers)
[![Fork](https://shields.io/github/forks/tugraph-family/chat2graph?logo=forgejo&label=Fork&color=orange)](https://github.com/TuGraph-family/chat2graph/forks)
[![Contributor](https://shields.io/github/contributors/tugraph-family/chat2graph?logo=actigraph&label=Contributor&color=abcdef)](https://github.com/TuGraph-family/chat2graph/contributors)
[![Commit](https://badgen.net/github/last-commit/tugraph-family/chat2graph/master?icon=git&label=Commit)](https://github.com/TuGraph-family/chat2graph/commits/master)
[![License](https://shields.io/github/license/tugraph-family/chat2graph?logo=apache&label=License&color=blue)](https://www.apache.org/licenses/LICENSE-2.0.html)
[![Release](https://shields.io/github/v/release/tugraph-family/chat2graph.svg?logo=stackblitz&label=Version&color=red)](https://github.com/TuGraph-family/chat2graph/releases)

## Background

Traditional tabular data processing technologies, such as distributed databases, data warehouses, 
and data lakes, have been continuously evolving and gradually maturing. In comparison, graph-based 
data processing technologies (graph databases, graph computing engines) provide new ideas and 
methods, but also face issues such as low ecological maturity and high barriers to product usage. 
With the rise of large language models (LLMs), how to effectively combine artificial intelligence 
technology with graph computing technology (Graph + AI) will be a very worthwhile direction to 
explore. On one hand, we can leverage cutting-edge technologies like LLMs and agents to 
lower the barriers to using graph computing products and enhance the user experience with graphs. 
On the other hand, graph computing technology can fully utilize the performance and 
interpretability advantages of graph data structures in relational analysis scenarios, assisting 
LLMs and intelligent agents in improving reasoning capabilities and generation quality.

## Introduction

Chat2Graph builds a multi-agent system (MAS) on top of a graph database to achieve intelligent 
capabilities in research and development, operations and maintenance, Q&A, generation, and more, 
helping users, developers, product managers, solution architects, operations engineers, and others 
to efficiently use graph databases, lower the barriers to using graphs, and accelerate content 
generation, implement dialogue with graphs. At the same time, leveraging the inherent advantages 
of graph data structures in relationship modeling, interpretability, etc., can enhance the key 
capabilities of intelligent agents such as reasoning, planning, memory, and tools, to achieve 
a deep integration of graph computing technology and artificial intelligence technology.

## Key Features

Chat2Graph currently provides basic capabilities of intelligent agent systems, but there are 
still many features that need to be improved together with the community.

- Reasoning && Planning
  - [x] One-Active-Many-Passive hybrid multi-agent architecture.
  - [x] Dual-LLM reasoning machine combining fast & slow thinking.
  - [x] Chain of agents (CoA) oriented task decomposition and graph planner.
  - [ ] Workflow auto-generation.
  - [ ] Action recommendation in operator.
  - [ ] Structured agent role management.
  - [ ] Agent task compiler.
- Memory && Knowledge
  - [x] Hierarchical memory system.
  - [x] Vector and graph knowledge base.
  - [ ] Knowledge refinement mechanism.
  - [ ] Environment management.
- Tool && System
  - [x] Toolkit knowledge graph.
  - [ ] Toolkit graph optimizer.
  - [ ] Rich toolkit/MCP integration.
  - [ ] Unified resource manager.
  - [ ] Tracing and control capabilities.
  - [ ] Benchmark.
- Product && Ecosystem
  - [x] Concise intelligent agent SDK.
  - [x] Web Service and interaction.
  - [x] One-click configuration of agents.
  - [ ] Multimodal capabilities.
  - [ ] Production enhancement.
  - [ ] Integration with open-source ecosystems.

## Quick Start

### Preparation

Prepare the required versions of Python and NodeJS.

* Install Python: [Python == 3.10](https://www.python.org/downloads) recommended.
* Install NodeJS: [NodeJS >= v16](https://nodejs.org/en/download) recommended.

You can also use tools like [conda][conda] to install the python environment.

### Build & Start

Build Chat2Graph as follows.

```bash
git clone https://github.com/TuGraph-family/chat2graph.git
cd chat2graph
./bin/build.sh
```

Then configure environment variables (e.g., LLM parameters) based on 
[.env.template](.env.template), startup Chat2Graph.

```bash
cp .env.template .env && vim .env
./bin/start.sh
```

When you see the following log:

```text
Starting server...
Web resources location: /Users/florian/code/chat2graph/app/server/web
System database url: sqlite:////Users/florian/.chat2graph/system/chat2graph.db
Loading AgenticService from app/core/sdk/chat2graph.yml with encoding utf-8
Init application: Chat2Graph
Init the Leader agent
Init the Expert agents
  ____ _           _   ____   ____                 _     
 / ___| |__   __ _| |_|___ \ / ___|_ __ __ _ _ __ | |__  
| |   | '_ \ / _` | __| __) | |  _| '__/ _` | '_ \| '_ \ 
| |___| | | | (_| | |_ / __/| |_| | | | (_| | |_) | | | |
 \____|_| |_|\__,_|\__|_____|\____|_|  \__,_| .__/|_| |_|
                                            |_|          

 * Serving Flask app 'bootstrap'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5010
 * Running on http://192.168.1.1:5010
Chat2Graph server started success ! (pid: 16483)
```

You can access Chat2Graph in the browser at [http://localhost:5010/](http://localhost:5010/):

![](doc/img/index.png)


## Register Graph Database

After registering the graph database to Chat2Graph in "Backend Manager", you can experience the complete ability 
of "chat to graph".
![](doc/img/gdb-mng.png)

The currently supported graph databases are:

* Neo4j

```bash
docker pull neo4j:latest
docker run -d -p 7474:7474 -p 7687:7687 --name neo4j-server --env NEO4J_AUTH=none \
  --env NEO4J_PLUGINS='["apoc", "graph-data-science"]' neo4j:latest
```

* TuGraph

```bash
docker pull tugraph/tugraph-runtime-centos7:4.5.1
docker run -d -p 7070:7070 -p 7687:7687 -p 9090:9090 --name tugraph-server \
  tugraph/tugraph-runtime-centos7:latest lgraph_server -d run --enable_plugin true
```

### Use SDK

The SDK of Chat2Graph provides a very clear and concise API, allowing you to easily build access 
to your intelligent system.

You can quickly converse with the built-in Chat2Graph in the following ways.

```python
SystemEnv.LLM_NAME="gpt-4o-mini"
SystemEnv.LLM_ENDPOINT="https://api.openai.com/v1"
SystemEnv.LLM_APIKEY="<YOUR-OPENAI-API-KEY>"

mas = AgenticService.load()
question = TextMessage(payload = "What is TuGraph ?")
answer = mas.execute(question).get_payload()
```

At the same time, the SDK also provides asynchronous dialogue capabilities.

```python
job = mas.session().submit(question)
answer = job.wait().get_payload()
```

Of course, customizing your own intelligent agent is also allowed.

```python
mas = AgenticService("Chat2Graph")
mas.expert(name="Design Expert").workflow(
        (analysis_operator, concept_modeling_operator)
    ).build()
```

To facilitate the rapid configuration of agents, you can describe the details of the agent 
using a YAML file and load it directly.

```python
mas = AgenticService.load("app/core/sdk/chat2graph.yml")
```

## Contributing

You can reference [Contributing][contrib] document and submit GitHub Issues/PRs 
to provide feedback and suggest improvements for Chat2Graph.

TuGraph establishes a clear [Architecture][arch] and [Roles][roles] for the community, and will 
invite outstanding contributors to join [SIGs][sigs].

## Contact

You can contact with us directly through TuGraph Discord and WeChat group provided below.

- Discord：https://discord.gg/KBCFbNFj
- WeChat：
![](https://github.com/TuGraph-family/community/blob/master/assets/contacts.png)

[conda]: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html
[contrib]: https://github.com/TuGraph-family/community/blob/master/docs/CONTRIBUTING.md
[arch]: https://github.com/TuGraph-family/community/blob/master/assets/arch.png
[roles]: https://github.com/TuGraph-family/community/blob/master/docs/ROLES.md
[sigs]: https://github.com/TuGraph-family/community/blob/master/docs/SIGS.md



