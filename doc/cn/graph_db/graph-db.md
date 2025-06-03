# 图数据库

Chat2Graph 可以与多个图数据库进行交互，并支持对它们的连接进行管理。

![](../img/graph-db-management.png)

+ **导航**： 通过管理侧边栏中的“图数据库管理”链接访问。
+ **搜索栏**： 可按名称或其他条件过滤数据库列表。
+ **新建按钮**： 打开表单或对话框以添加新的图数据库连接。通常需要提供名称、数据库地址（例如 Neo4j 的 localhost:7687）、凭证，以及可能选择默认模式。
+ **数据库列表**： 以表格形式显示已配置的图数据库，包含以下列：
  + **图数据库名称**： 用户定义的连接名称（例如 my_db）。带有“默认”标签表示该数据库在未指定其他选项时将作为默认使用。
  + **图数据库地址**： 数据库实例的网络地址和端口。
  + **默认图模式**：（如适用，显示与此连接关联的默认模式名称）。
  + **最后修改时间**： 连接配置最后一次更新的时戳。
  + **操作**： 对每个数据库连接可用的操作：
    + **编辑**： 修改连接详细信息。
    + **删除**： 移除数据库连接。
    + **设为默认**： 将此数据库连接标记为默认使用的连接。
+ **注意事项**： 在对话中，如需 Chat2Graph 与图数据库顺畅协作，请确保已创建默认图数据库。

## 图数据库安装

在 Chat2Graph 与默认图数据库交互之前，请确保在本地或远程安装并设置好图数据库。

当前 Docker 支持的图数据库有：

+ Neo4j

```bash
docker pull neo4j:latest
docker run -d -p 7474:7474 -p 7687:7687 --name neo4j-server --env NEO4J_AUTH=none \
  --env NEO4J_PLUGINS='["apoc", "graph-data-science"]' neo4j:latest
```

+ TuGraph-DB

**注意**：我们将在未来支持 TuGraph-DB 的连接。

```bash
docker pull tugraph/tugraph-runtime-centos7:4.5.1
docker run -d -p 7070:7070 -p 7687:7687 -p 9090:9090 --name tugraph-server \
  tugraph/tugraph-runtime-centos7:latest lgraph_server -d run --enable_plugin true
```
