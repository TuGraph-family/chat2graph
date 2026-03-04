"""
Agentic Text2GQL Usage Example

演示如何使用 Agentic Text2GQL 系统将自然语言转换为 Cypher 查询。

Author: kaichuan
Date: 2025-11-25
"""

import asyncio

from app.core.model.job import Job
from app.core.service.query_context_service import QueryContextService


async def example_simple_query():
    """示例 1: 简单查询 - 查找 Person 节点"""
    print("=" * 80)
    print("示例 1: 简单查询")
    print("=" * 80)

    # Create query session
    context_service = QueryContextService.instance
    session = context_service.create_session(
        user_id="example_user_001",
        initial_context={"query_source": "example_script"}
    )

    # Natural language query
    natural_query = "Find all Person nodes named 'John'"

    # Create Job (intentionally unused - for demonstration only)
    _job = Job(
        goal=natural_query,
        context="Simple vertex query example",
        session_id=session.session_id
    )

    # Execute query
    print(f"\n自然语言查询: {natural_query}")
    print(f"会话 ID: {session.session_id}")
    print("\n开始执行...")

    # Note: Actual execution requires full Agent initialization
    # result = await sdk.run(_job)
    # print(f"\n查询结果:\n{result}")

    print("\n示例 1 完成")


async def example_complex_query():
    """示例 2: 复杂查询 - 多跳关系查询"""
    print("\n" + "=" * 80)
    print("示例 2: 复杂多跳查询")
    print("=" * 80)

    context_service = QueryContextService.instance

    # Create session
    session = context_service.create_session(user_id="example_user_002")

    # Complex query: friends of friends
    natural_query = "Find friends of friends of John who work at Tech companies"

    # Create Job (intentionally unused - for demonstration only)
    _job = Job(
        goal=natural_query,
        context="Multi-hop relationship query with filtering",
        session_id=session.session_id
    )

    print(f"\n自然语言查询: {natural_query}")
    print(f"会话 ID: {session.session_id}")
    print("\n预期执行流程:")
    print("1. 查询意图分析 - 识别多跳模式")
    print("2. 复杂度分析 - 评估为 MODERATE/COMPLEX")
    print("3. 路径模式识别 - MULTI_HOP, depth=2")
    print("4. 上下文增强 - 检索相似历史查询")
    print("5. 查询设计 - 生成优化的 Cypher")
    print("6. 查询验证 - Schema, 语义, 性能, 安全")
    print("7. 查询执行 - 返回结果")

    print("\n示例 2 完成")


async def example_temporal_query():
    """示例 3: 时间查询"""
    print("\n" + "=" * 80)
    print("示例 3: 时间约束查询")
    print("=" * 80)

    context_service = QueryContextService.instance
    session = context_service.create_session(user_id="example_user_003")

    # Temporal query
    natural_query = "Find all projects created in the last year"

    # Create Job (intentionally unused - for demonstration only)
    _job = Job(
        goal=natural_query,
        context="Temporal query with relative time constraint",
        session_id=session.session_id
    )

    print(f"\n自然语言查询: {natural_query}")
    print(f"会话 ID: {session.session_id}")
    print("\n预期时间条件生成:")
    print("- 时间表达式: 'in the last year'")
    print("- Unix 时间戳范围: start_timestamp -> end_timestamp")
    print("- Cypher 条件: created_at >= <start> AND created_at <= <end>")

    print("\n示例 3 完成")


async def example_spatial_query():
    """示例 4: 空间查询"""
    print("\n" + "=" * 80)
    print("示例 4: 空间约束查询")
    print("=" * 80)

    context_service = QueryContextService.instance
    session = context_service.create_session(user_id="example_user_004")

    # Spatial query
    natural_query = "Find all stores within 5 km of Beijing"

    # Create Job (intentionally unused - for demonstration only)
    _job = Job(
        goal=natural_query,
        context="Spatial query with distance constraint",
        session_id=session.session_id
    )

    print(f"\n自然语言查询: {natural_query}")
    print(f"会话 ID: {session.session_id}")
    print("\n预期空间条件生成:")
    print("- 空间表达式: 'within 5 km'")
    print("- 中心点: Beijing (需要地理编码)")
    print("- Cypher 条件: distance(point(...), point(...)) <= 5000")

    print("\n示例 4 完成")


async def example_with_context():
    """示例 5: 利用上下文优化查询"""
    print("\n" + "=" * 80)
    print("示例 5: 上下文感知查询")
    print("=" * 80)

    context_service = QueryContextService.instance

    # Create session and execute multiple queries to build history
    session = context_service.create_session(user_id="example_user_005")

    # Simulate historical queries
    print("\n模拟建立查询历史...")
    queries = [
        "Find Person nodes",
        "Find Person nodes with age > 25",
        "Find Person nodes named 'Alice'",
    ]

    for query_text in queries:
        # Save query history (simplified example)
        context_service.save_query(
            session_id=session.session_id,
            user_id="example_user_005",
            query_text=query_text,
            query_cypher=f"MATCH (p:Person) RETURN p  -- for {query_text}",
            success=True,
            latency_ms=150
        )
        print(f"  - {query_text}")

    # Execute new query, should leverage context
    natural_query = "Find Person nodes with name containing 'Bob'"

    # Create Job (intentionally unused - for demonstration only)
    _job = Job(
        goal=natural_query,
        context="Query with historical context",
        session_id=session.session_id
    )

    print(f"\n新查询: {natural_query}")
    print(f"会话 ID: {session.session_id}")
    print("\n预期上下文增强:")
    print("- 检索到 3 个相似历史查询")
    print("- 学习用户偏好: preferred_complexity=SIMPLE")
    print("- 查询建议: 使用类似的 MATCH 模式")
    print("- 性能优化: 添加 LIMIT（根据历史模式）")

    print("\n示例 5 完成")


async def example_validation_workflow():
    """示例 6: 查询验证工作流"""
    print("\n" + "=" * 80)
    print("示例 6: 查询验证工作流")
    print("=" * 80)

    context_service = QueryContextService.instance
    session = context_service.create_session(user_id="example_user_006")

    # A query that may have issues
    natural_query = "Find all Person and Company nodes"

    # Create Job (intentionally unused - for demonstration only)
    _job = Job(
        goal=natural_query,
        context="Query that may have validation issues",
        session_id=session.session_id
    )

    print(f"\n自然语言查询: {natural_query}")
    print(f"会话 ID: {session.session_id}")
    print("\n预期验证流程:")
    print("\n1. Schema 验证:")
    print("   - 检查 Person 和 Company 是否存在")
    print("   - 验证属性访问")
    print("   - 结果: PASS (假设类型存在)")

    print("\n2. 语义检查:")
    print("   - 检测到笛卡尔积风险（两个独立的 MATCH）")
    print("   - 警告: 可能返回大量结果")
    print("   - 建议: 添加连接条件或 LIMIT")

    print("\n3. 性能预测:")
    print("   - 估算延迟: 500-2000ms (HIGH tier)")
    print("   - 瓶颈: 笛卡尔积")
    print("   - 建议: 添加 WHERE 连接条件")

    print("\n4. 安全扫描:")
    print("   - 资源滥用风险: MEDIUM (缺少 LIMIT)")
    print("   - 建议: 添加 LIMIT 子句")

    print("\n5. 最终建议:")
    print("   - 动作: APPROVE_WITH_WARNINGS")
    print("   - 必需修改: 添加 LIMIT 1000")
    print("   - 可选优化: 添加连接条件")

    print("\n示例 6 完成")


async def example_full_workflow():
    """示例 7: 完整的 Agentic 工作流"""
    print("\n" + "=" * 80)
    print("示例 7: 完整的 Agentic Text2GQL 工作流")
    print("=" * 80)

    context_service = QueryContextService.instance
    session = context_service.create_session(user_id="example_user_007")

    natural_query = "Find the shortest path between Person 'Alice' and Company 'TechCorp'"

    # Create Job (intentionally unused - for demonstration only)
    _job = Job(
        goal=natural_query,
        context="Complex path finding query",
        session_id=session.session_id
    )

    print(f"\n自然语言查询: {natural_query}")
    print(f"会话 ID: {session.session_id}")
    print("\n完整执行流程:")

    print("\n[Stage 1: Understand and Analyze]")
    print("  Operator 1: 查询意图分析")
    print("    - action: find")
    print("    - object_vertex_types: ['Person', 'Company']")
    print("    - query_conditions: [name='Alice', name='TechCorp']")
    print("    - pattern_type: SHORTEST_PATH")

    print("\n  Operator 2: 复杂度分析")
    print("    - complexity_level: COMPLEX")
    print("    - complexity_score: 0.75")
    print("    - recommended_strategy: Multi-stage with shortestPath()")
    print("    - index_recommendations: [name:btree for Person and Company]")

    print("\n  Operator 3: 路径模式识别")
    print("    - pattern_type: SHORTEST_PATH")
    print("    - source_entity: Person")
    print("    - target_entity: Company")
    print("    - bidirectional: false")

    print("\n[Stage 2: Enhance with Context]")
    print("  Operator 4: 上下文增强")
    print("    - relevant_history: 0 条 (新用户)")
    print("    - user_preferences: {} (空)")
    print("    - suggestions: 使用 shortestPath() 函数")

    print("\n[Stage 3: Design Query]")
    print("  Operator 5: 查询设计")
    print("    - designed_query:")
    print("      MATCH (a:Person {name: 'Alice'}), (b:Company {name: 'TechCorp'})")
    print("      MATCH p = shortestPath((a)-[*]-(b))")
    print("      RETURN p")
    print("    - optimization: 使用 shortestPath() 算法")

    print("\n[Stage 4: Validate]")
    print("  Operator 6: 查询验证")
    print("    - schema_validation: PASS")
    print("    - semantic_validation: PASS")
    print("    - performance_prediction: MEDIUM tier (200-500ms)")
    print("    - security_scan: LOW risk")
    print("    - final_recommendation: APPROVE")

    print("\n[Stage 5: Execute]")
    print("  Operator 7: 查询执行")
    print("    - execution_status: SUCCESS")
    print("    - query_result: [Path with 3 nodes, 2 relationships]")
    print("    - execution_stats: {latency_ms: 320, result_count: 1}")

    print("\n[Post-Execution]")
    print("  - 保存查询历史到数据库")
    print("  - 更新用户偏好（如果启用学习）")
    print("  - 记录性能指标用于未来优化")

    print("\n示例 7 完成")


async def main():
    """运行所有示例"""
    print("\n")
    print("*" * 80)
    print("Agentic Text2GQL 使用示例")
    print("*" * 80)
    print("\n这些示例演示了如何使用 Agentic Text2GQL 系统")
    print("注意：这些是概念示例，实际执行需要完整的系统初始化")

    # 运行所有示例
    await example_simple_query()
    await example_complex_query()
    await example_temporal_query()
    await example_spatial_query()
    await example_with_context()
    await example_validation_workflow()
    await example_full_workflow()

    print("\n" + "=" * 80)
    print("所有示例完成！")
    print("=" * 80)

    print("\n\n如何运行实际系统:")
    print("1. 启动 TuGraph 数据库")
    print("2. 配置数据库连接（app/server/config/）")
    print("3. 运行迁移脚本创建数据表")
    print("4. 使用 Chat2Graph SDK 或 API 执行查询")

    print("\n\nSDK 使用示例:")
    print("```python")
    print("from app.core.sdk.chat2graph import Chat2Graph")
    print("")
    print("# 初始化")
    print('c2g = Chat2Graph(config_path="config/agent_workflows/agentic_text2gql.yml")')
    print("")
    print("# 执行查询")
    print('result = await c2g.run("Find all Person nodes named John")')
    print("print(result)")
    print("```")


if __name__ == "__main__":
    asyncio.run(main())
