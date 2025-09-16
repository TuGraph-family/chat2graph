# Chat2Graph - 图原生智能体系统

## 项目简介 (Project Introduction)

Chat2Graph 是一个**图原生智能体系统 (Graph Native Agentic System)**，利用多智能体架构和图数据库技术，实现了高效的任务分解、推理和协作。该项目采用"一主多从"混合多智能体架构 (One-Active-Many-Passive hybrid multi-agent architecture)，结合双 LLM 推理机制 (Dual-LLM reasoning machine)，提供快慢思考相结合的智能决策能力。

## 核心特性列表 (Core Features)

### 🧠 推理与规划 (Reasoning & Planning)
- ✅ **一主多从混合多智能体架构** - 实现高效的任务分发和协作
- ✅ **双 LLM 推理机制** - 结合快思考和慢思考的推理模式
- ✅ **面向智能体链的任务分解** - Chain of Agents (CoA) 导向的图规划器
- 🔄 **工作流自动生成** - 基于任务需求的动态工作流构建
- 🔄 **操作建议系统** - 智能化的操作推荐机制

### 🧐 记忆与知识 (Memory & Knowledge)
- ✅ **分层记忆系统 (Hierarchical Memory System)** - 多级记忆管理机制
- ✅ **向量和图知识库** - 结合向量检索和图结构的知识存储
- 🔄 **知识精炼机制** - 自动化的知识提取和优化
- 🔄 **环境管理系统** - 智能体运行环境的统一管理

### 🔧 工具与系统 (Tool & System)
- ✅ **工具包知识图谱** - 工具能力的图结构化表示
- 🔄 **工具图优化器** - 智能化工具选择和组合
- 🔄 **丰富的工具包/MCP 集成** - 扩展的工具集成能力
- 🔄 **统一资源管理器** - 系统资源的集中化管理
- 🔄 **跟踪和控制能力** - 全链路的执行监控

### 🎯 产品与生态 (Product & Ecosystem)
- ✅ **简洁的智能体 SDK** - 开发友好的软件开发包
- ✅ **Web 服务和交互界面** - 完整的 Web 应用支持
- ✅ **一键配置智能体** - 简化的智能体部署流程
- 🔄 **多模态能力** - 支持文本、图像等多种模态
- 🔄 **生产级增强** - 企业级部署和优化特性

## 技术栈 (Tech Stack)

### 后端核心 (Backend Core)
- **Python 3.10-3.11** - 主要开发语言
- **Poetry** - 依赖管理和虚拟环境
- **Pydantic 2.x** - 数据验证和序列化
- **SQLAlchemy** - 关系型数据库 ORM (Object-Relational Mapping)

### AI 与推理 (AI & Reasoning)
- **OpenAI API** - 大语言模型服务
- **AISuite** - 多模型集成框架
- **LiteLLM** - LLM 代理和路由
- **DBGpt** - 数据库增强的 GPT 集成

### 知识与存储 (Knowledge & Storage)
- **Neo4j** - 图数据库
- **ChromaDB** - 向量数据库
- **NetworkX** - 图计算和分析
- **TuGraph** - 高性能图数据库

### Web 服务 (Web Services)
- **Flask** - Web 应用框架
- **Flask-SQLAlchemy** - Flask 数据库集成
- **Flask-CORS** - 跨域资源共享

### 开发工具 (Development Tools)
- **Pytest** - 单元测试框架
- **Ruff** - 代码格式化和 Linting
- **MyPy** - 静态类型检查
- **Poetry** - 项目管理

## Wiki 导航 (Wiki Navigation)

### 📚 基础文档
- [**安装与配置指南**](Installation.md) - 环境搭建、安装步骤和配置说明

### 🏗️ 架构设计
- [**架构总览**](Architecture/Overview.md) - 系统整体架构和设计理念
- [**智能体模块**](Architecture/Module-Agent.md) - 智能体系统核心组件
- [**推理器模块**](Architecture/Module-Reasoner.md) - 推理引擎架构设计
- [**工作流模块**](Architecture/Module-Workflow.md) - 工作流编排系统
- [**知识库模块**](Architecture/Module-Knowledge.md) - 知识存储和检索系统
- [**服务层模块**](Architecture/Module-Service.md) - 核心业务服务

### 💻 代码深度分析
- [**代码精粹分析**](Code-Analysis/Highlights.md) - 优秀设计模式和实现亮点
- [**潜在问题与改进建议**](Code-Analysis/Issues-and-Suggestions.md) - 代码质量分析和优化建议

### 🧪 测试体系
- [**测试指南**](Testing/Guide.md) - 测试架构、用例和执行方法

---

## 快速开始

```bash
# 克隆项目
git clone https://github.com/TuGraph-family/chat2graph.git

# 安装依赖
cd chat2graph
poetry install

# 启动服务
poetry run python -m app.server.bootstrap
```

更详细的安装和使用说明请参考 [安装与配置指南](Installation.md)。

---

🌐️ **English** | [中文](doc/zh-cn/readme.md) | 📖 [官方文档](https://chat2graph.vercel.app)