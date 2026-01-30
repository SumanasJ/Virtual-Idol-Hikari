"""
系统测试脚本
测试所有核心组件是否正常工作
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_config():
    """测试配置系统"""
    print("\n" + "="*60)
    print("1️⃣ 测试配置系统")
    print("="*60)

    try:
        from config.settings import settings
        from config.prompts import IDOL_PERSONA

        print("✅ 配置模块导入成功")

        # 验证配置
        validation = settings.validate()
        if validation["valid"]:
            print("✅ 配置验证通过")
        else:
            print("❌ 配置验证失败:")
            for error in validation["errors"]:
                print(f"   - {error}")
            return False

        # 显示配置
        print(f"\n当前配置:")
        print(f"  LLM Provider: {settings.LLM_PROVIDER}")
        print(f"  Model: {settings.MODEL_NAME}")
        print(f"  Neo4j URI: {settings.NEO4J_URI[:30]}...")

        print(f"\n偶像人设:")
        print(f"  名字: {IDOL_PERSONA['name']}")
        print(f"  年龄: {IDOL_PERSONA['age']}")
        print(f"  风格: {IDOL_PERSONA['speaking_style'][:30]}...")

        return True

    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        return False


def test_llm_manager():
    """测试 LLM 管理器"""
    print("\n" + "="*60)
    print("2️⃣ 测试 LLM 管理器")
    print("="*60)

    try:
        from core.llm.llm_manager import get_llm_manager

        llm_manager = get_llm_manager()
        print("✅ LLM 管理器初始化成功")
        print(f"  Provider: {llm_manager.provider}")

        # 测试简单生成
        print("\n测试简单生成...")
        response = llm_manager.generate("说'你好'")
        print(f"✅ 生成成功: {response[:50]}...")

        return True

    except Exception as e:
        print(f"❌ LLM 管理器测试失败: {e}")
        return False


def test_vector_store():
    """测试向量存储"""
    print("\n" + "="*60)
    print("3️⃣ 测试向量存储")
    print("="*60)

    try:
        from core.memory.vector_store import get_vector_store

        vector_store = get_vector_store()
        print("✅ 向量存储初始化成功")

        # 测试添加和搜索
        print("\n测试添加对话...")
        vector_store.add_conversation(
            session_id="test",
            user_message="你好，我是测试用户",
            assistant_message="你好！很高兴见到你~"
        )
        print("✅ 对话添加成功")

        print("\n测试相似性搜索...")
        results = vector_store.search(
            query="测试",
            session_id="test",
            k=1
        )
        print(f"✅ 搜索成功，找到 {len(results)} 条结果")

        # 显示统计
        stats = vector_store.get_stats()
        print(f"\n统计信息:")
        print(f"  总文档数: {stats.get('total_documents', 0)}")

        return True

    except Exception as e:
        print(f"❌ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph():
    """测试知识图谱"""
    print("\n" + "="*60)
    print("4️⃣ 测试知识图谱")
    print("="*60)

    try:
        from core.memory.graph_manager import get_kg_manager

        kg_manager = get_kg_manager()
        print("✅ 知识图谱管理器初始化成功")
        print(f"  Neo4j URI: {kg_manager.uri[:30]}...")

        # 测试抽取和存储
        print("\n测试实体抽取...")
        dialogue = "用户: 我喜欢摇滚音乐\n偶像: 真的吗？我也很喜欢！"
        stats = kg_manager.extract_and_store(
            dialogue=dialogue,
            session_id="test"
        )
        print(f"✅ 抽取成功: {stats}")

        # 测试查询
        print("\n测试图查询...")
        results = kg_manager.query_relevant_subgraph(
            query_text="音乐",
            session_id="test"
        )
        print(f"✅ 查询成功，找到 {len(results)} 条结果")

        # 显示统计
        stats = kg_manager.get_stats()
        print(f"\n统计信息:")
        print(f"  总节点数: {stats.get('total_nodes', 0)}")
        print(f"  总关系数: {stats.get('total_relationships', 0)}")

        return True

    except Exception as e:
        print(f"❌ 知识图谱测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_personality_system():
    """测试性格系统"""
    print("\n" + "="*60)
    print("5️⃣ 测试性格系统")
    print("="*60)

    try:
        from core.personality.personality_model import create_personality_model
        from core.personality.trait_evolver import create_personality_evolver

        # 创建模型
        personality_model = create_personality_model()
        print("✅ 性格模型初始化成功")

        # 显示初始状态
        state = personality_model.get_current_state()
        print(f"\n初始性格:")
        print(f"  开朗度: {state.cheerfulness:.2f}")
        print(f"  温柔度: {state.gentleness:.2f}")
        print(f"  元气值: {state.energy:.2f}")

        # 创建进化器
        evolver = create_personality_evolver(personality_model)
        print("✅ 性格进化器初始化成功")

        # 测试进化
        print("\n测试性格进化...")
        evolver.evolve("今天心情特别好！")
        new_state = personality_model.get_current_state()
        print(f"✅ 进化成功")
        print(f"  进化次数: {new_state.evolution_count}")

        return True

    except Exception as e:
        print(f"❌ 性格系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent():
    """测试完整代理"""
    print("\n" + "="*60)
    print("6️⃣ 测试完整代理")
    print("="*60)

    try:
        from core.agent.langgraph_agent import VirtualIdolAgent

        # 创建代理
        agent = VirtualIdolAgent(session_id="test_session")
        print("✅ 代理初始化成功")

        # 测试对话
        print("\n测试对话...")
        response = agent.chat("你好！")
        print(f"✅ 对话成功")
        print(f"  响应: {response[:50]}...")

        # 再次测试（验证记忆）
        print("\n测试第二次对话...")
        response2 = agent.chat("我叫什么名字？")
        print(f"✅ 第二次对话成功")
        print(f"  响应: {response2[:50]}...")

        return True

    except Exception as e:
        print(f"❌ 代理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🎭 AI 虚拟偶像 Demo - 系统测试")
    print("="*60)

    results = []

    # 运行所有测试
    results.append(("配置系统", test_config()))
    results.append(("LLM 管理器", test_llm_manager()))
    results.append(("向量存储", test_vector_store()))
    results.append(("知识图谱", test_knowledge_graph()))
    results.append(("性格系统", test_personality_system()))
    results.append(("完整代理", test_agent()))

    # 显示总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常运行。")
        print("\n启动应用:")
        print("  streamlit run app.py")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置和依赖。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
