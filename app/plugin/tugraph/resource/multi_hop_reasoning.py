"""
Multi-Hop Reasoning Tools

提供路径模式识别、时间查询构建和空间查询构建工具。

Author: kaichuan
Date: 2025-11-25
"""

import re
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict

from app.core.toolkit.tool import Tool


class PatternType(str, Enum):
    """路径模式类型"""
    DIRECT = "DIRECT"
    MULTI_HOP = "MULTI_HOP"
    VARIABLE_LENGTH = "VARIABLE_LENGTH"
    SHORTEST_PATH = "SHORTEST_PATH"
    PATTERN_MATCH = "PATTERN_MATCH"


@dataclass
class PathPattern:
    """路径模式数据类"""
    pattern_type: str
    source_entity: str
    target_entity: str
    relationship_types: List[str]
    min_depth: int = 1
    max_depth: int = 1
    bidirectional: bool = False
    temporal_constraints: Optional[Dict[str, Any]] = None
    spatial_constraints: Optional[Dict[str, Any]] = None
    pattern_constraints: Optional[List[Dict[str, Any]]] = None


class PathPatternRecognizer(Tool):
    """Tool for identifying complex path patterns in natural language queries."""

    # 路径模式指示器
    SHORTEST_PATH_KEYWORDS = [
        'shortest', 'fastest', 'quickest', 'most direct', 'minimum',
        '最短', '最快', '最直接', '最少'
    ]

    MULTI_HOP_KEYWORDS = [
        'through', 'via', 'connected to', 'related to', 'chain',
        '通过', '经过', '连接到', '相关的', '链'
    ]

    VARIABLE_LENGTH_KEYWORDS = [
        'any number of', 'multiple', 'several', 'friends of friends',
        'variable', 'flexible',
        '任意数量', '多个', '若干', '朋友的朋友', '可变'
    ]

    BIDIRECTIONAL_KEYWORDS = [
        'between', 'connecting', 'linking', 'mutual', 'both ways',
        '之间', '相互', '双向'
    ]

    def __init__(self):
        super().__init__(
            name=self.recognize_patterns.__name__,
            description=self.recognize_patterns.__doc__ or "",
            function=self.recognize_patterns,
        )

    async def recognize_patterns(
        self,
        query: str,
        intention_analysis: Dict[str, Any]
    ) -> str:
        """Identify complex path patterns in the natural language query.

        Args:
            query (str): The natural language query
            intention_analysis (dict): Structured intention analysis containing:
                - object_vertex_types (list): List of entity types involved
                - query_conditions (list): List of query conditions

        Returns:
            str: JSON string containing:
                - has_multi_hop (bool): Whether multi-hop reasoning is required
                - patterns (list): List of identified path patterns, each containing:
                    - pattern_type (str): Type of pattern (DIRECT, MULTI_HOP, etc.)
                    - source_entity (str): Source entity type
                    - target_entity (str): Target entity type
                    - relationship_types (list): Types of relationships
                    - min_depth (int): Minimum traversal depth
                    - max_depth (int): Maximum traversal depth
                    - bidirectional (bool): Whether path is bidirectional
                    - temporal_constraints (dict): Time-based constraints
                    - spatial_constraints (dict): Location-based constraints
                    - pattern_constraints (list): Additional pattern constraints

        Example:
            result = await recognize_patterns(
                query="Find shortest path between Person A and Person B through Company",
                intention_analysis={
                    "object_vertex_types": ["Person", "Company"],
                    "query_conditions": []
                }
            )
        """
        query_lower = query.lower()
        patterns = []

        # 提取实体
        entities = intention_analysis.get('object_vertex_types', [])

        if len(entities) < 2:
            # 单实体查询 - 无路径模式
            result = {
                "has_multi_hop": False,
                "patterns": []
            }
            import json
            return json.dumps(result, ensure_ascii=False, indent=2)

        # 检测模式类型
        is_shortest = self._contains_keywords(query_lower, self.SHORTEST_PATH_KEYWORDS)
        is_multi_hop = self._contains_keywords(query_lower, self.MULTI_HOP_KEYWORDS)
        is_variable_length = self._contains_keywords(query_lower, self.VARIABLE_LENGTH_KEYWORDS)
        is_bidirectional = self._contains_keywords(query_lower, self.BIDIRECTIONAL_KEYWORDS)

        # 确定模式类型和深度
        if is_shortest:
            pattern_type = PatternType.SHORTEST_PATH.value
            min_depth, max_depth = 1, 10  # 合理默认值
        elif is_variable_length:
            pattern_type = PatternType.VARIABLE_LENGTH.value
            min_depth, max_depth = self._extract_depth_range(query_lower)
        elif is_multi_hop:
            pattern_type = PatternType.MULTI_HOP.value
            hop_count = self._estimate_hop_count(query_lower)
            min_depth = max_depth = hop_count
        else:
            pattern_type = PatternType.DIRECT.value
            min_depth = max_depth = 1

        # 提取关系类型
        relationship_types = self._extract_relationships(query_lower)

        # 为每对实体创建模式
        for i in range(len(entities) - 1):
            source = entities[i]
            target = entities[i + 1]

            pattern = PathPattern(
                pattern_type=pattern_type,
                source_entity=source,
                target_entity=target,
                relationship_types=relationship_types,
                min_depth=min_depth,
                max_depth=max_depth,
                bidirectional=is_bidirectional,
                temporal_constraints=self._extract_temporal_constraints(query_lower),
                spatial_constraints=self._extract_spatial_constraints(query_lower),
                pattern_constraints=[]
            )

            patterns.append(asdict(pattern))

        has_multi_hop = (
            pattern_type != PatternType.DIRECT.value or
            len(patterns) > 1
        )

        result = {
            "has_multi_hop": has_multi_hop,
            "patterns": patterns
        }

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """检查文本是否包含任何关键词"""
        return any(keyword in text for keyword in keywords)

    def _estimate_hop_count(self, query: str) -> int:
        """从查询文本估算跳数"""
        # 统计连接词
        connectors = ['through', 'via', 'to', 'of', 'and', '通过', '到', '和']
        count = sum(query.count(c) for c in connectors)
        return max(2, min(5, count + 1))

    def _extract_depth_range(self, query: str) -> tuple:
        """提取可变长度路径的深度范围"""
        # 查找数字模式
        numbers = re.findall(r'\d+', query)

        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return 1, int(numbers[0])
        else:
            return 1, 5  # 默认范围

    def _extract_relationships(self, query: str) -> List[str]:
        """从查询中提取关系类型"""
        # 常见关系模式
        rel_patterns = [
            'friend', 'follow', 'work', 'know', 'member',
            'own', 'manage', 'create', 'belong', 'contain',
            '朋友', '关注', '工作', '认识', '成员', '拥有', '管理', '创建'
        ]

        found_rels = []
        for rel in rel_patterns:
            if rel in query:
                # 转换为 Cypher 约定的大写形式
                cypher_rel = rel.upper()
                if not query.count(rel + 's'):
                    cypher_rel += 'S_WITH'
                found_rels.append(cypher_rel)

        return found_rels if found_rels else ['*']  # 如果未找到则使用通配符

    def _extract_temporal_constraints(self, query: str) -> Optional[Dict[str, Any]]:
        """从查询中提取时间约束"""
        constraints = {}

        # 简单的时间模式
        if 'in' in query and any(year in query for year in ['2020', '2021', '2022', '2023', '2024', '2025']):
            year_match = re.search(r'202\d', query)
            if year_match:
                constraints['year'] = int(year_match.group())

        if 'last' in query or '最近' in query or '上一个' in query:
            if 'year' in query or '年' in query:
                constraints['relative'] = 'last_year'
            elif 'month' in query or '月' in query:
                constraints['relative'] = 'last_month'
            elif 'week' in query or '周' in query or '星期' in query:
                constraints['relative'] = 'last_week'

        if 'between' in query or '之间' in query:
            # 提取日期范围
            date_pattern = r'(\d{4}-\d{2}-\d{2})'
            dates = re.findall(date_pattern, query)
            if len(dates) >= 2:
                constraints['start_date'] = dates[0]
                constraints['end_date'] = dates[1]

        return constraints if constraints else None

    def _extract_spatial_constraints(self, query: str) -> Optional[Dict[str, Any]]:
        """从查询中提取空间约束"""
        constraints = {}

        # 距离模式
        distance_match = re.search(r'(\d+)\s*(km|mile|meter|公里|米)', query)
        if distance_match:
            constraints['distance'] = int(distance_match.group(1))
            unit = distance_match.group(2)
            if unit in ['km', '公里']:
                constraints['unit'] = 'km'
            elif unit in ['mile']:
                constraints['unit'] = 'mile'
            else:
                constraints['unit'] = 'meter'

        # 位置模式
        if 'near' in query or 'around' in query or '附近' in query or '周围' in query:
            constraints['proximity'] = True

        if 'within' in query or '在...内' in query or '范围内' in query:
            constraints['within'] = True

        return constraints if constraints else None


class TemporalQueryBuilder(Tool):
    """Tool for building temporal queries from natural language time expressions."""

    def __init__(self):
        super().__init__(
            name=self.build_temporal_query.__name__,
            description=self.build_temporal_query.__doc__ or "",
            function=self.build_temporal_query,
        )

    async def build_temporal_query(
        self,
        temporal_expression: str,
        property_name: str = "created_at"
    ) -> str:
        """Build Cypher temporal query components from natural language time expressions.

        Args:
            temporal_expression (str): Natural language time expression, such as:
                - "in 2024"
                - "last year"
                - "between 2023-01-01 and 2023-12-31"
                - "in the past 30 days"
                - "before 2024-06-01"
            property_name (str, optional): The name of the temporal property to filter on

        Returns:
            str: JSON string containing:
                - cypher_condition (str): Cypher WHERE condition for temporal filtering
                - cypher_function (str): Cypher temporal function to use
                - start_timestamp (int, optional): Start timestamp in Unix format
                - end_timestamp (int, optional): End timestamp in Unix format
                - explanation (str): Human-readable explanation of the temporal filter

        Example:
            result = await build_temporal_query(
                temporal_expression="in the last year",
                property_name="created_at"
            )
        """
        import time
        from datetime import datetime, timedelta

        expr = temporal_expression.lower()
        now = datetime.now()
        result = {}

        # 模式 1: 具体年份
        year_match = re.search(r'in\s+(\d{4})', expr)
        if year_match:
            year = int(year_match.group(1))
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31, 23, 59, 59)
            result = {
                "cypher_condition": f"{property_name} >= {int(start.timestamp())} AND {property_name} <= {int(end.timestamp())}",
                "cypher_function": f"datetime({{epochSeconds: {property_name}}})",
                "start_timestamp": int(start.timestamp()),
                "end_timestamp": int(end.timestamp()),
                "explanation": f"筛选 {year} 年的记录"
            }

        # 模式 2: 相对时间（last year, last month, etc.）
        elif 'last year' in expr or '去年' in expr or '上一年' in expr:
            start = datetime(now.year - 1, 1, 1)
            end = datetime(now.year - 1, 12, 31, 23, 59, 59)
            result = {
                "cypher_condition": f"{property_name} >= {int(start.timestamp())} AND {property_name} <= {int(end.timestamp())}",
                "cypher_function": f"datetime({{epochSeconds: {property_name}}})",
                "start_timestamp": int(start.timestamp()),
                "end_timestamp": int(end.timestamp()),
                "explanation": f"筛选去年（{now.year - 1}）的记录"
            }

        elif 'last month' in expr or '上个月' in expr:
            # 计算上个月
            first_day_this_month = now.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)

            result = {
                "cypher_condition": f"{property_name} >= {int(first_day_last_month.timestamp())} AND {property_name} <= {int(last_day_last_month.timestamp())}",
                "cypher_function": f"datetime({{epochSeconds: {property_name}}})",
                "start_timestamp": int(first_day_last_month.timestamp()),
                "end_timestamp": int(last_day_last_month.timestamp()),
                "explanation": "筛选上个月的记录"
            }

        # 模式 3: 过去 N 天/周/月
        past_match = re.search(r'(?:past|last)\s+(\d+)\s+(day|week|month|year)s?', expr)
        if past_match and not result:
            count = int(past_match.group(1))
            unit = past_match.group(2)

            if unit == 'day':
                delta = timedelta(days=count)
                unit_zh = '天'
            elif unit == 'week':
                delta = timedelta(weeks=count)
                unit_zh = '周'
            elif unit == 'month':
                delta = timedelta(days=count * 30)  # 近似
                unit_zh = '月'
            else:  # year
                delta = timedelta(days=count * 365)  # 近似
                unit_zh = '年'

            start = now - delta
            result = {
                "cypher_condition": f"{property_name} >= {int(start.timestamp())}",
                "cypher_function": f"datetime({{epochSeconds: {property_name}}})",
                "start_timestamp": int(start.timestamp()),
                "end_timestamp": int(now.timestamp()),
                "explanation": f"筛选过去 {count} {unit_zh}的记录"
            }

        # 模式 4: 日期范围（between A and B）
        date_range = re.search(r'between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})', expr)
        if date_range and not result:
            start_date = datetime.strptime(date_range.group(1), '%Y-%m-%d')
            end_date = datetime.strptime(date_range.group(2), '%Y-%m-%d')

            result = {
                "cypher_condition": f"{property_name} >= {int(start_date.timestamp())} AND {property_name} <= {int(end_date.timestamp())}",
                "cypher_function": f"datetime({{epochSeconds: {property_name}}})",
                "start_timestamp": int(start_date.timestamp()),
                "end_timestamp": int(end_date.timestamp()),
                "explanation": f"筛选 {date_range.group(1)} 到 {date_range.group(2)} 之间的记录"
            }

        # 模式 5: before/after 特定日期
        before_match = re.search(r'before\s+(\d{4}-\d{2}-\d{2})', expr)
        after_match = re.search(r'after\s+(\d{4}-\d{2}-\d{2})', expr)

        if before_match and not result:
            date = datetime.strptime(before_match.group(1), '%Y-%m-%d')
            result = {
                "cypher_condition": f"{property_name} < {int(date.timestamp())}",
                "cypher_function": f"datetime({{epochSeconds: {property_name}}})",
                "end_timestamp": int(date.timestamp()),
                "explanation": f"筛选 {before_match.group(1)} 之前的记录"
            }

        if after_match and not result:
            date = datetime.strptime(after_match.group(1), '%Y-%m-%d')
            result = {
                "cypher_condition": f"{property_name} > {int(date.timestamp())}",
                "cypher_function": f"datetime({{epochSeconds: {property_name}}})",
                "start_timestamp": int(date.timestamp()),
                "explanation": f"筛选 {after_match.group(1)} 之后的记录"
            }

        # 如果没有匹配到任何模式
        if not result:
            result = {
                "cypher_condition": "",
                "cypher_function": "",
                "explanation": f"无法解析时间表达式: {temporal_expression}"
            }

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)


class SpatialQueryBuilder(Tool):
    """Tool for building spatial queries from natural language location expressions."""

    def __init__(self):
        super().__init__(
            name=self.build_spatial_query.__name__,
            description=self.build_spatial_query.__doc__ or "",
            function=self.build_spatial_query,
        )

    async def build_spatial_query(
        self,
        spatial_expression: str,
        latitude_property: str = "latitude",
        longitude_property: str = "longitude"
    ) -> str:
        """Build Cypher spatial query components from natural language location expressions.

        Args:
            spatial_expression (str): Natural language spatial expression, such as:
                - "within 10 km"
                - "near Beijing"
                - "around location X"
                - "between 10 and 50 miles"
            latitude_property (str, optional): Name of the latitude property
            longitude_property (str, optional): Name of the longitude property

        Returns:
            str: JSON string containing:
                - cypher_condition (str): Cypher WHERE condition for spatial filtering
                - cypher_function (str): Cypher spatial function to use
                - distance (float, optional): Distance value
                - distance_unit (str, optional): Unit of distance (km, mile, meter)
                - center_point (dict, optional): Center point for proximity search
                - explanation (str): Human-readable explanation of the spatial filter

        Example:
            result = await build_spatial_query(
                spatial_expression="within 10 km of Beijing",
                latitude_property="lat",
                longitude_property="lon"
            )
        """
        expr = spatial_expression.lower()
        result = {}

        # 模式 1: within X km/miles
        within_match = re.search(r'within\s+(\d+(?:\.\d+)?)\s*(km|mile|meter|公里|米)', expr)
        if within_match:
            distance = float(within_match.group(1))
            unit = within_match.group(2)

            # 单位转换
            if unit in ['km', '公里']:
                distance_km = distance
                unit_str = 'km'
            elif unit == 'mile':
                distance_km = distance * 1.60934
                unit_str = 'mile'
            else:  # meter or 米
                distance_km = distance / 1000
                unit_str = 'meter'

            result = {
                "cypher_condition": f"distance(point({{latitude: {latitude_property}, longitude: {longitude_property}}}), point({{latitude: $center_lat, longitude: $center_lon}})) <= {distance_km * 1000}",
                "cypher_function": "point(), distance()",
                "distance": distance,
                "distance_unit": unit_str,
                "center_point": {
                    "parameter": "$center_lat, $center_lon",
                    "note": "需要提供中心点坐标参数"
                },
                "explanation": f"筛选距离中心点 {distance} {unit_str} 范围内的记录"
            }

        # 模式 2: near [location]
        elif 'near' in expr or '附近' in expr:
            # 默认半径 5km
            default_radius_km = 5

            result = {
                "cypher_condition": f"distance(point({{latitude: {latitude_property}, longitude: {longitude_property}}}), point({{latitude: $center_lat, longitude: $center_lon}})) <= {default_radius_km * 1000}",
                "cypher_function": "point(), distance()",
                "distance": default_radius_km,
                "distance_unit": "km",
                "center_point": {
                    "parameter": "$center_lat, $center_lon",
                    "note": "需要提供中心点坐标参数，默认半径 5km"
                },
                "explanation": f"筛选附近（默认 {default_radius_km} km 范围内）的记录"
            }

        # 模式 3: between X and Y km
        range_match = re.search(r'between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)\s*(km|mile|meter)', expr)
        if range_match and not result:
            min_dist = float(range_match.group(1))
            max_dist = float(range_match.group(2))
            unit = range_match.group(3)

            # 单位转换
            if unit == 'km':
                min_dist_m = min_dist * 1000
                max_dist_m = max_dist * 1000
            elif unit == 'mile':
                min_dist_m = min_dist * 1609.34
                max_dist_m = max_dist * 1609.34
            else:  # meter
                min_dist_m = min_dist
                max_dist_m = max_dist

            result = {
                "cypher_condition": f"distance(point({{latitude: {latitude_property}, longitude: {longitude_property}}}), point({{latitude: $center_lat, longitude: $center_lon}})) >= {min_dist_m} AND distance(point({{latitude: {latitude_property}, longitude: {longitude_property}}}), point({{latitude: $center_lat, longitude: $center_lon}})) <= {max_dist_m}",
                "cypher_function": "point(), distance()",
                "min_distance": min_dist,
                "max_distance": max_dist,
                "distance_unit": unit,
                "center_point": {
                    "parameter": "$center_lat, $center_lon",
                    "note": "需要提供中心点坐标参数"
                },
                "explanation": f"筛选距离中心点 {min_dist} 到 {max_dist} {unit} 范围内的记录"
            }

        # 如果没有匹配到任何模式
        if not result:
            result = {
                "cypher_condition": "",
                "cypher_function": "",
                "explanation": f"无法解析空间表达式: {spatial_expression}，建议使用 'within X km' 或 'near location' 格式"
            }

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)
