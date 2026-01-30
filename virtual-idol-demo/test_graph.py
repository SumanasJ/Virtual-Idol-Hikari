"""
测试知识图谱功能
"""

import sys
sys.path.insert(0, '/Users/sue/CodingGround/virtual-idol-demo')

from core.memory.graph_manager import get_kg_manager

print("="*60)
print("测试知识图谱功能")
print("="*60)

try:
    # 初始化
    kg_manager = get_kg_manager()
    print("\n✅ 知识图谱管理器初始化成功")

    # 测试抽取和存储
    print("\n测试 1: 抽取对话")
    dialogue = """
    用户: 我喜欢吃章鱼烧
    偶像: 真的吗？我也很喜欢章鱼烧！
    用户: 我还喜欢去大阪旅行
    偶像: 大阪太棒了！
    """

    stats = kg_manager.extract_and_store(
        dialogue=dialogue,
        session_id="test_session"
    )
    print(f"抽取结果: {stats}")

    # 测试获取图数据
    print("\n测试 2: 获取图数据")
    graph_data = kg_manager.get_graph_data(session_id="test_session")
    print(f"节点数: {len(graph_data['nodes'])}")
    print(f"边数: {len(graph_data['edges'])}")

    if graph_data['nodes']:
        print("\n节点列表:")
        for node in graph_data['nodes'][:5]:
            print(f"  - {node['label']} ({node['group']})")

    if graph_data['edges']:
        print("\n边列表:")
        for edge in graph_data['edges'][:5]:
            print(f"  - {edge['from']} -> {edge['to']} ({edge['label']})")

    # 测试统计
    print("\n测试 3: 获取统计信息")
    stats = kg_manager.get_stats()
    print(f"总节点数: {stats.get('total_nodes', 0)}")
    print(f"总关系数: {stats.get('total_relationships', 0)}")

    print("\n✅ 所有测试通过！")

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
