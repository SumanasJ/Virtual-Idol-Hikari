"""
检查 Neo4j 中的实际节点结构
"""

import sys
sys.path.insert(0, '/Users/sue/CodingGround/virtual-idol-demo')

from core.memory.graph_manager import get_kg_manager

print("检查 Neo4j 节点结构...")

kg_manager = get_kg_manager()

# 查看所有节点及其属性
cypher = """
MATCH (n)
RETURN n, properties(n) AS props
LIMIT 5
"""

results = kg_manager.graph.query(cypher)

print(f"\n找到 {len(results)} 个节点:\n")

for i, record in enumerate(results[:5], 1):
    print(f"节点 {i}:")
    print(f"  完整对象: {record['n']}")
    print(f"  属性: {record['props']}")
    print()
