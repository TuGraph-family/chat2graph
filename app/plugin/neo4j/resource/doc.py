QUERY_GRAMMER = """
===== 图vertex查询语法书 =====
简单例子：
MATCH (p:种类 {筛选条件}) RETURN p
MATCH (p:种类), (q:种类) WHERE p,q的条件 RETURN p,q
=====
"""
