"""
Query Validation Tools

提供查询验证工具，包括Schema合规性验证、语义检查、性能预测和安全扫描。

Author: kaichuan
Date: 2025-11-25
"""

import re
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from app.core.toolkit.tool import Tool
from app.core.service.graph_db_service import GraphDbService


@dataclass
class ValidationResult:
    """验证结果数据结构"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    severity: str  # INFO, WARNING, ERROR, CRITICAL


class SchemaValidator(Tool):
    """Tool for validating Cypher queries against graph schema."""

    def __init__(self):
        super().__init__(
            name=self.validate_schema.__name__,
            description=self.validate_schema.__doc__ or "",
            function=self.validate_schema,
        )

    async def validate_schema(
        self,
        graph_db_service: GraphDbService,
        cypher_query: str,
        strict_mode: bool = False
    ) -> str:
        """Validate a Cypher query against the graph database schema.

        Args:
            graph_db_service (GraphDbService): Graph database service instance
            cypher_query (str): The Cypher query to validate
            strict_mode (bool, optional): Enable strict validation mode

        Returns:
            str: JSON string containing validation result:
                - is_valid (bool): Whether the query is schema-compliant
                - errors (list): List of schema violation errors
                - warnings (list): List of potential issues
                - suggestions (list): List of improvement suggestions
                - severity (str): Overall severity level
                - schema_info (dict): Relevant schema information

        Example:
            result = await validate_schema(
                graph_db_service=service,
                cypher_query="MATCH (p:Person) RETURN p",
                strict_mode=False
            )
        """
        errors = []
        warnings = []
        suggestions = []

        # 获取 schema
        try:
            query = "CALL dbms.graph.getGraphSchema()"
            store = graph_db_service.get_default_graph_db()
            schema_result = store.conn.run(query=query)
            schema = json.loads(schema_result[0][0])["schema"]
        except Exception as e:
            errors.append(f"无法获取 schema: {str(e)}")
            result = ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                suggestions=["检查数据库连接"],
                severity="CRITICAL"
            )
            return json.dumps(
                {"validation": asdict(result), "schema_info": None},
                ensure_ascii=False,
                indent=2
            )

        # 提取查询中的顶点类型和属性
        vertex_types = self._extract_vertex_types(cypher_query)
        property_accesses = self._extract_property_accesses(cypher_query)

        # 构建 schema 映射
        schema_map = self._build_schema_map(schema)

        # 验证顶点类型
        for vertex_type in vertex_types:
            if vertex_type not in schema_map:
                errors.append(f"顶点类型 '{vertex_type}' 不存在于 schema 中")
                suggestions.append(f"可用的顶点类型: {', '.join(schema_map.keys())}")

        # 验证属性访问
        for var, vertex_type, prop in property_accesses:
            if vertex_type and vertex_type in schema_map:
                properties = schema_map[vertex_type]
                if prop not in properties:
                    if strict_mode:
                        errors.append(
                            f"属性 '{prop}' 不存在于顶点类型 '{vertex_type}' 中"
                        )
                    else:
                        warnings.append(
                            f"属性 '{prop}' 可能不存在于顶点类型 '{vertex_type}' 中"
                        )
                    suggestions.append(
                        f"顶点类型 '{vertex_type}' 的可用属性: {', '.join(properties)}"
                    )

        # 检查语法错误
        syntax_issues = self._check_syntax(cypher_query)
        errors.extend(syntax_issues)

        # 确定严重程度
        if errors:
            severity = "ERROR" if not strict_mode else "CRITICAL"
        elif warnings:
            severity = "WARNING"
        else:
            severity = "INFO"

        result = ValidationResult(
            is_valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            severity=severity
        )

        return json.dumps(
            {
                "validation": asdict(result),
                "schema_info": {
                    "available_vertex_types": list(schema_map.keys()),
                    "vertex_types_in_query": vertex_types,
                    "properties_accessed": property_accesses
                }
            },
            ensure_ascii=False,
            indent=2
        )

    def _extract_vertex_types(self, query: str) -> List[str]:
        """提取查询中的顶点类型"""
        # 匹配模式: (var:Type) 或 (:Type)
        pattern = r'\((?:\w+)?:(\w+)[^\)]*\)'
        matches = re.findall(pattern, query)
        return list(set(matches))

    def _extract_property_accesses(self, query: str) -> List[tuple]:
        """提取属性访问: (变量, 顶点类型, 属性名)"""
        accesses = []

        # 匹配模式: var.property
        prop_pattern = r'(\w+)\.(\w+)'
        prop_matches = re.findall(prop_pattern, query)

        # 匹配变量到类型的映射: (var:Type)
        type_pattern = r'\((\w+):(\w+)[^\)]*\)'
        type_matches = re.findall(type_pattern, query)
        var_to_type = {var: vtype for var, vtype in type_matches}

        for var, prop in prop_matches:
            vertex_type = var_to_type.get(var)
            accesses.append((var, vertex_type, prop))

        return accesses

    def _build_schema_map(self, schema: List[Dict]) -> Dict[str, List[str]]:
        """构建顶点类型到属性列表的映射"""
        schema_map = {}
        for item in schema:
            if item.get("type") == "VERTEX":
                label = item.get("label", "")
                properties = [prop.get("name", "") for prop in item.get("properties", [])]
                schema_map[label] = properties
        return schema_map

    def _check_syntax(self, query: str) -> List[str]:
        """检查基本语法错误"""
        errors = []

        # 检查必需关键字
        if "MATCH" not in query.upper() and "CREATE" not in query.upper():
            errors.append("查询缺少 MATCH 或 CREATE 子句")

        if "RETURN" not in query.upper() and "DELETE" not in query.upper() and "SET" not in query.upper():
            errors.append("查询缺少 RETURN、DELETE 或 SET 子句")

        # 检查括号匹配
        if query.count("(") != query.count(")"):
            errors.append("括号不匹配")

        if query.count("{") != query.count("}"):
            errors.append("花括号不匹配")

        if query.count("[") != query.count("]"):
            errors.append("方括号不匹配")

        return errors


class SemanticChecker(Tool):
    """Tool for checking semantic correctness of Cypher queries."""

    def __init__(self):
        super().__init__(
            name=self.check_semantics.__name__,
            description=self.check_semantics.__doc__ or "",
            function=self.check_semantics,
        )

    async def check_semantics(
        self,
        cypher_query: str,
        query_intention: Optional[Dict[str, Any]] = None
    ) -> str:
        """Check the semantic correctness of a Cypher query.

        Args:
            cypher_query (str): The Cypher query to check
            query_intention (dict, optional): User's query intention for alignment check

        Returns:
            str: JSON string containing semantic check result:
                - is_semantically_valid (bool): Whether query is semantically correct
                - semantic_issues (list): List of semantic problems
                - logic_warnings (list): List of logic warnings
                - intention_alignment (dict): How well query matches intention
                - recommendations (list): Improvement recommendations

        Example:
            result = await check_semantics(
                cypher_query="MATCH (p:Person) WHERE p.age > 18 RETURN p",
                query_intention={"action": "find", "object": "Person", "conditions": ["age > 18"]}
            )
        """
        issues = []
        warnings = []
        recommendations = []

        # 检查变量使用
        variable_issues = self._check_variable_usage(cypher_query)
        issues.extend(variable_issues)

        # 检查逻辑一致性
        logic_warnings = self._check_logic_consistency(cypher_query)
        warnings.extend(logic_warnings)

        # 检查常见反模式
        anti_patterns = self._detect_anti_patterns(cypher_query)
        warnings.extend(anti_patterns)

        # 如果提供了意图，检查对齐度
        alignment = None
        if query_intention:
            alignment = self._check_intention_alignment(cypher_query, query_intention)
            if alignment.get("misalignment_score", 0) > 0.3:
                warnings.append("查询可能不完全符合用户意图")
                recommendations.extend(alignment.get("suggestions", []))

        # 生成推荐
        if not recommendations:
            recommendations = self._generate_recommendations(cypher_query)

        result = {
            "is_semantically_valid": len(issues) == 0,
            "semantic_issues": issues,
            "logic_warnings": warnings,
            "intention_alignment": alignment,
            "recommendations": recommendations
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    def _check_variable_usage(self, query: str) -> List[str]:
        """检查变量使用的语义问题"""
        issues = []

        # 提取所有变量定义 (var:Type)
        defined_vars = set(re.findall(r'\((\w+):\w+[^\)]*\)', query))

        # 提取所有变量使用 (var.prop, RETURN var, WHERE var)
        used_vars = set()
        # var.property 模式
        used_vars.update(re.findall(r'(\w+)\.\w+', query))
        # RETURN 子句中的变量
        return_match = re.search(r'RETURN\s+(.*?)(?:$|ORDER|LIMIT|;)', query, re.IGNORECASE)
        if return_match:
            return_vars = re.findall(r'\b(\w+)\b', return_match.group(1))
            used_vars.update([v for v in return_vars if not v.upper() in ['AS', 'DISTINCT']])

        # 检查未定义的变量
        undefined_vars = used_vars - defined_vars
        if undefined_vars:
            issues.append(f"使用了未定义的变量: {', '.join(undefined_vars)}")

        # 检查未使用的变量
        unused_vars = defined_vars - used_vars
        if unused_vars:
            issues.append(f"定义但未使用的变量: {', '.join(unused_vars)}")

        return issues

    def _check_logic_consistency(self, query: str) -> List[str]:
        """检查逻辑一致性"""
        warnings = []

        # 检查矛盾的条件
        where_match = re.search(r'WHERE\s+(.*?)(?:RETURN|$)', query, re.IGNORECASE)
        if where_match:
            conditions = where_match.group(1)
            # 检查 AND 连接的矛盾条件（简化版）
            if 'AND' in conditions.upper():
                # 例如: age > 30 AND age < 20
                warnings.append("请检查 WHERE 条件是否存在逻辑矛盾")

        # 检查空结果的可能性
        if "WHERE" in query.upper() and "OR" not in query.upper():
            warnings.append("多个 AND 条件可能导致空结果集")

        return warnings

    def _detect_anti_patterns(self, query: str) -> List[str]:
        """检测常见反模式"""
        warnings = []

        # 反模式 1: 缺少 LIMIT
        if "RETURN" in query.upper() and "LIMIT" not in query.upper():
            warnings.append("查询缺少 LIMIT 子句，可能返回大量结果")

        # 反模式 2: SELECT *
        if re.search(r'RETURN\s+\*', query, re.IGNORECASE):
            warnings.append("使用 RETURN * 可能返回不必要的数据")

        # 反模式 3: 笛卡尔积
        match_count = len(re.findall(r'MATCH', query, re.IGNORECASE))
        if match_count > 1 and "WHERE" not in query.upper():
            warnings.append("多个 MATCH 子句未连接可能产生笛卡尔积")

        return warnings

    def _check_intention_alignment(
        self,
        query: str,
        intention: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查查询与用户意图的对齐度"""
        misalignments = []
        suggestions = []

        # 检查动作对齐
        action = intention.get("action", "").lower()
        if action == "find" and "RETURN" not in query.upper():
            misalignments.append("意图是查找，但查询缺少 RETURN")
            suggestions.append("添加 RETURN 子句返回结果")

        if action == "create" and "CREATE" not in query.upper():
            misalignments.append("意图是创建，但查询缺少 CREATE")
            suggestions.append("使用 CREATE 子句创建节点或关系")

        # 检查对象对齐
        object_types = intention.get("object_vertex_types", [])
        query_types = re.findall(r':(\w+)', query)
        missing_types = set(object_types) - set(query_types)
        if missing_types:
            misalignments.append(f"意图中的类型 {missing_types} 未出现在查询中")

        misalignment_score = len(misalignments) / max(3, len(intention))

        return {
            "misalignment_score": misalignment_score,
            "misalignments": misalignments,
            "suggestions": suggestions
        }

    def _generate_recommendations(self, query: str) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if "LIMIT" not in query.upper():
            recommendations.append("建议添加 LIMIT 子句限制结果数量")

        if "INDEX" not in query.upper() and "WHERE" in query.upper():
            recommendations.append("考虑为过滤条件添加索引提示")

        return recommendations


class PerformancePredictor(Tool):
    """Tool for predicting query performance."""

    def __init__(self):
        super().__init__(
            name=self.predict_performance.__name__,
            description=self.predict_performance.__doc__ or "",
            function=self.predict_performance,
        )

    async def predict_performance(
        self,
        cypher_query: str,
        complexity_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Predict the performance characteristics of a Cypher query.

        Args:
            cypher_query (str): The Cypher query to analyze
            complexity_analysis (dict, optional): Pre-computed complexity analysis

        Returns:
            str: JSON string containing performance prediction:
                - estimated_latency_ms (int): Predicted query latency
                - estimated_memory_mb (int): Predicted memory usage
                - performance_tier (str): LOW, MEDIUM, HIGH, CRITICAL
                - bottlenecks (list): Identified performance bottlenecks
                - optimization_opportunities (list): Performance improvement suggestions
                - resource_warnings (list): Resource usage warnings

        Example:
            result = await predict_performance(
                cypher_query="MATCH (p:Person)-[:KNOWS*1..5]->(f) RETURN p, f",
                complexity_analysis={"complexity_level": "COMPLEX"}
            )
        """
        # 基础性能指标（启发式估计）
        base_latency = 50  # ms
        base_memory = 10   # MB

        bottlenecks = []
        optimizations = []
        warnings = []

        # 分析查询特征
        features = self._extract_query_features(cypher_query)

        # 根据特征预测性能
        latency_multiplier = 1.0
        memory_multiplier = 1.0

        # 因素 1: 可变长度路径
        if features["has_variable_length"]:
            max_depth = features.get("max_path_depth", 5)
            latency_multiplier *= (1.5 ** max_depth)
            memory_multiplier *= (1.3 ** max_depth)
            bottlenecks.append("可变长度路径查询可能导致组合爆炸")
            optimizations.append("限制路径深度范围或添加过滤条件")

        # 因素 2: 缺少 LIMIT
        if not features["has_limit"]:
            latency_multiplier *= 1.5
            memory_multiplier *= 2.0
            bottlenecks.append("缺少 LIMIT 可能返回大量结果")
            optimizations.append("添加 LIMIT 子句限制结果集大小")

        # 因素 3: 笛卡尔积
        if features["cartesian_product_risk"]:
            latency_multiplier *= 3.0
            memory_multiplier *= 4.0
            bottlenecks.append("可能存在笛卡尔积")
            optimizations.append("添加 WHERE 条件连接 MATCH 模式")

        # 因素 4: 聚合操作
        if features["has_aggregation"]:
            latency_multiplier *= 1.2
            memory_multiplier *= 1.5
            optimizations.append("考虑在聚合前添加过滤条件")

        # 因素 5: 复杂度分析
        if complexity_analysis:
            complexity_level = complexity_analysis.get("complexity_level", "SIMPLE")
            if complexity_level == "MODERATE":
                latency_multiplier *= 1.3
            elif complexity_level == "COMPLEX":
                latency_multiplier *= 2.0
                memory_multiplier *= 1.8

        # 计算预测值
        estimated_latency = int(base_latency * latency_multiplier)
        estimated_memory = int(base_memory * memory_multiplier)

        # 确定性能等级
        if estimated_latency < 100:
            tier = "LOW"
        elif estimated_latency < 500:
            tier = "MEDIUM"
        elif estimated_latency < 2000:
            tier = "HIGH"
        else:
            tier = "CRITICAL"
            warnings.append("查询可能需要超过 2 秒执行")

        # 内存警告
        if estimated_memory > 100:
            warnings.append(f"预计内存使用 {estimated_memory} MB，可能影响系统稳定性")

        result = {
            "estimated_latency_ms": estimated_latency,
            "estimated_memory_mb": estimated_memory,
            "performance_tier": tier,
            "bottlenecks": bottlenecks,
            "optimization_opportunities": optimizations,
            "resource_warnings": warnings,
            "confidence": "MEDIUM"  # 启发式预测的置信度
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    def _extract_query_features(self, query: str) -> Dict[str, Any]:
        """提取查询特征用于性能预测"""
        features = {}

        # 可变长度路径
        var_length_match = re.search(r'\[.*?\*(\d+)?\.\.(\d+)?\]', query)
        features["has_variable_length"] = bool(var_length_match)
        if var_length_match:
            max_depth = var_length_match.group(2)
            features["max_path_depth"] = int(max_depth) if max_depth else 5

        # LIMIT 子句
        features["has_limit"] = "LIMIT" in query.upper()

        # 聚合函数
        agg_functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "COLLECT"]
        features["has_aggregation"] = any(func in query.upper() for func in agg_functions)

        # 笛卡尔积风险
        match_count = len(re.findall(r'MATCH', query, re.IGNORECASE))
        has_where = "WHERE" in query.upper()
        features["cartesian_product_risk"] = (match_count > 1 and not has_where)

        # MATCH 数量
        features["match_count"] = match_count

        return features


class SecurityScanner(Tool):
    """Tool for scanning Cypher queries for security vulnerabilities."""

    def __init__(self):
        super().__init__(
            name=self.scan_security.__name__,
            description=self.scan_security.__doc__ or "",
            function=self.scan_security,
        )

    async def scan_security(
        self,
        cypher_query: str,
        query_source: str = "user_input"
    ) -> str:
        """Scan a Cypher query for security vulnerabilities.

        Args:
            cypher_query (str): The Cypher query to scan
            query_source (str, optional): Source of the query (user_input, generated, trusted)

        Returns:
            str: JSON string containing security scan result:
                - is_safe (bool): Whether query is safe to execute
                - vulnerabilities (list): Detected security vulnerabilities
                - risk_level (str): LOW, MEDIUM, HIGH, CRITICAL
                - injection_risk (dict): Cypher injection risk analysis
                - resource_abuse_risk (dict): Resource abuse potential
                - data_exposure_risk (dict): Data exposure concerns
                - recommendations (list): Security improvement recommendations

        Example:
            result = await scan_security(
                cypher_query="MATCH (u:User) WHERE u.name = 'admin' RETURN u",
                query_source="user_input"
            )
        """
        vulnerabilities = []
        recommendations = []

        # 检查注入风险
        injection_risk = self._check_injection_risk(cypher_query, query_source)
        if injection_risk["risk_score"] > 0.5:
            vulnerabilities.append({
                "type": "CYPHER_INJECTION",
                "severity": "HIGH",
                "description": "查询可能存在 Cypher 注入风险",
                "details": injection_risk
            })
            recommendations.append("使用参数化查询替代字符串拼接")

        # 检查资源滥用
        resource_risk = self._check_resource_abuse(cypher_query)
        if resource_risk["risk_score"] > 0.6:
            vulnerabilities.append({
                "type": "RESOURCE_ABUSE",
                "severity": "MEDIUM",
                "description": "查询可能导致资源滥用",
                "details": resource_risk
            })
            recommendations.extend(resource_risk.get("mitigations", []))

        # 检查数据暴露
        exposure_risk = self._check_data_exposure(cypher_query)
        if exposure_risk["risk_score"] > 0.4:
            vulnerabilities.append({
                "type": "DATA_EXPOSURE",
                "severity": "MEDIUM",
                "description": "查询可能暴露敏感数据",
                "details": exposure_risk
            })
            recommendations.append("添加适当的访问控制和数据过滤")

        # 检查危险操作
        dangerous_ops = self._check_dangerous_operations(cypher_query)
        if dangerous_ops:
            vulnerabilities.append({
                "type": "DANGEROUS_OPERATION",
                "severity": "HIGH",
                "description": "查询包含危险操作",
                "details": {"operations": dangerous_ops}
            })
            recommendations.append("限制或审计危险操作的执行")

        # 确定风险等级
        if not vulnerabilities:
            risk_level = "LOW"
        else:
            severity_scores = {
                "LOW": 1,
                "MEDIUM": 2,
                "HIGH": 3,
                "CRITICAL": 4
            }
            max_severity = max(
                severity_scores.get(v["severity"], 0)
                for v in vulnerabilities
            )
            risk_level = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}[max_severity]

        result = {
            "is_safe": (risk_level in ["LOW", "MEDIUM"]),
            "vulnerabilities": vulnerabilities,
            "risk_level": risk_level,
            "injection_risk": injection_risk,
            "resource_abuse_risk": resource_risk,
            "data_exposure_risk": exposure_risk,
            "recommendations": recommendations
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    def _check_injection_risk(self, query: str, source: str) -> Dict[str, Any]:
        """检查 Cypher 注入风险"""
        risk_score = 0.0
        indicators = []

        # 来源风险
        if source == "user_input":
            risk_score += 0.3
            indicators.append("查询来源于用户输入")

        # 动态字符串拼接迹象
        if "+" in query or "CONCAT" in query.upper():
            risk_score += 0.4
            indicators.append("可能使用了字符串拼接")

        # 缺少参数化
        if "$" not in query and source == "user_input":
            risk_score += 0.3
            indicators.append("未使用参数化查询")

        return {
            "risk_score": min(1.0, risk_score),
            "indicators": indicators,
            "mitigation": "使用参数化查询 ($param) 替代字符串拼接"
        }

    def _check_resource_abuse(self, query: str) -> Dict[str, Any]:
        """检查资源滥用风险"""
        risk_score = 0.0
        issues = []
        mitigations = []

        # 缺少 LIMIT
        if "LIMIT" not in query.upper():
            risk_score += 0.4
            issues.append("缺少 LIMIT 限制")
            mitigations.append("添加 LIMIT 子句")

        # 可变长度路径
        if re.search(r'\*\d*\.\.\d*', query):
            risk_score += 0.3
            issues.append("包含可变长度路径")
            mitigations.append("限制路径深度范围")

        # 笛卡尔积
        match_count = len(re.findall(r'MATCH', query, re.IGNORECASE))
        if match_count > 1 and "WHERE" not in query.upper():
            risk_score += 0.4
            issues.append("可能产生笛卡尔积")
            mitigations.append("添加 WHERE 连接条件")

        return {
            "risk_score": min(1.0, risk_score),
            "issues": issues,
            "mitigations": mitigations
        }

    def _check_data_exposure(self, query: str) -> Dict[str, Any]:
        """检查数据暴露风险"""
        risk_score = 0.0
        concerns = []

        # 返回所有属性
        if re.search(r'RETURN\s+\*', query, re.IGNORECASE):
            risk_score += 0.3
            concerns.append("使用 RETURN * 可能暴露不必要的数据")

        # 返回敏感类型
        sensitive_keywords = ["password", "token", "secret", "key", "credential"]
        for keyword in sensitive_keywords:
            if keyword in query.lower():
                risk_score += 0.5
                concerns.append(f"查询涉及敏感字段: {keyword}")

        # 缺少过滤条件
        if "WHERE" not in query.upper() and "RETURN" in query.upper():
            risk_score += 0.2
            concerns.append("缺少 WHERE 条件可能返回所有数据")

        return {
            "risk_score": min(1.0, risk_score),
            "concerns": concerns,
            "recommendation": "添加适当的数据过滤和字段选择"
        }

    def _check_dangerous_operations(self, query: str) -> List[str]:
        """检查危险操作"""
        dangerous = []

        # DELETE 操作
        if "DELETE" in query.upper():
            dangerous.append("DELETE - 删除操作")

        # DETACH DELETE
        if "DETACH DELETE" in query.upper():
            dangerous.append("DETACH DELETE - 级联删除操作")

        # SET 修改
        if "SET" in query.upper():
            dangerous.append("SET - 数据修改操作")

        # REMOVE
        if "REMOVE" in query.upper():
            dangerous.append("REMOVE - 属性删除操作")

        # DROP
        if "DROP" in query.upper():
            dangerous.append("DROP - 可能的 schema 修改")

        return dangerous
