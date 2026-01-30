"""
聊天界面组件
提供类似 ChatGPT 的对话界面
"""

import streamlit as st
from typing import List, Dict, Any
from datetime import datetime


def render_chat_message(role: str, content: str, avatar: str = None) -> None:
    """
    渲染聊天消息

    Args:
        role: 角色（user/assistant）
        content: 消息内容
        avatar: 头像
    """
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)


def render_chat_history(
    messages: List[Dict[str, str]],
    show_avatars: bool = True
) -> None:
    """
    渲染聊天历史

    Args:
        messages: 消息列表
        show_avatars: 是否显示头像
    """
    for msg in messages:
        avatar = None
        if show_avatars:
            if msg["role"] == "user":
                avatar = "👤"
            else:
                avatar = "🎭"

        render_chat_message(msg["role"], msg["content"], avatar)


def render_personality_panel(personality: Dict[str, Any]) -> None:
    """
    渲染性格状态面板

    Args:
        personality: 性格状态字典
    """
    st.markdown("## 🎭 性格状态")

    # 进度条配置
    traits_config = {
        "cheerfulness": {"label": "开朗度", "emoji": "😊", "color": "🟢"},
        "gentleness": {"label": "温柔度", "emoji": "💗", "color": "🌸"},
        "energy": {"label": "元气值", "emoji": "⚡", "color": "💛"},
        "curiosity": {"label": "好奇心", "emoji": "🔍", "color": "💜"},
        "empathy": {"label": "同理心", "emoji": "🤝", "color": "💙"}
    }

    # 显示各维度
    for trait_key, config in traits_config.items():
        value = personality.get(trait_key, 0.5)
        percentage = int(value * 100)

        st.markdown(
            f"""
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>{config['emoji']} {config['label']}</span>
                    <span>{percentage}%</span>
                </div>
                <div style="background-color: #262730; border-radius: 5px; padding: 3px;">
                    <div style="background: linear-gradient(90deg, #4CAF50, #8BC34A);
                               width: {percentage}%; height: 8px; border-radius: 5px;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 进化次数
    evolution_count = personality.get("evolution_count", 0)
    st.markdown(f"**进化次数**: {evolution_count}")

    # 最后更新时间
    last_updated = personality.get("last_updated", "")
    if last_updated:
        try:
            dt = datetime.fromisoformat(last_updated)
            time_str = dt.strftime("%H:%M:%S")
            st.caption(f"最后更新: {time_str}")
        except:
            pass


def render_session_stats(agent) -> None:
    """
    渲染会话统计信息

    Args:
        agent: 虚拟偶像代理实例
    """
    st.markdown("## 📊 会话统计")

    # 对话轮数
    chat_history = agent.chat_history
    num_turns = len(chat_history) // 2
    st.metric("对话轮数", num_turns)

    # 知识图谱统计
    try:
        kg_data = agent.get_kg_data()
        num_nodes = len(kg_data.get("nodes", []))
        num_edges = len(kg_data.get("edges", []))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("图节点", num_nodes)
        with col2:
            st.metric("图关系", num_edges)
    except:
        st.warning("无法获取知识图谱统计")


def render_idol_profile() -> None:
    """渲染偶像资料卡"""
    from config.prompts import IDOL_PERSONA

    st.markdown("## 🌟 偶像资料")

    # 基本信息
    st.markdown(f"**名字**: {IDOL_PERSONA['name']}")
    st.markdown(f"**年龄**: {IDOL_PERSONA['age']} 岁")
    st.markdown(f"**说话风格**: {IDOL_PERSONA['speaking_style']}")

    st.markdown("---")

    # 背景
    st.markdown("### 📖 背景故事")
    st.markdown(IDOL_PERSONA['background'])

    st.markdown("---")

    # 兴趣爱好
    st.markdown("### ❤️ 兴趣爱好")
    for interest in IDOL_PERSONA['interests']:
        st.markdown(f"- {interest}")

    # 不喜欢的
    if IDOL_PERSONA.get('dislikes'):
        st.markdown("### 💔 不喜欢的")
        for dislike in IDOL_PERSONA['dislikes']:
            st.markdown(f"- {dislike}")


def render_suggested_questions() -> None:
    """渲染建议问题"""
    st.markdown("### 💭 试试问这些")

    suggestions = [
        "介绍一下你自己吧！",
        "你喜欢什么类型的音乐？",
        "我最近心情不太好...",
        "有什么推荐的旅行地点吗？",
        "你还记得我之前说过什么吗？"
    ]

    for suggestion in suggestions:
        if st.button(suggestion, key=f"suggestion_{suggestion}"):
            st.session_state.suggested_question = suggestion
            st.rerun()


def render_system_info() -> None:
    """渲染系统信息"""
    from config.settings import settings

    with st.expander("⚙️ 系统信息"):
        st.markdown(f"**LLM Provider**: {settings.LLM_PROVIDER}")
        st.markdown(f"**Model**: {settings.MODEL_NAME}")
        st.markdown(f"**Session ID**: {settings.SESSION_ID}")

        # Neo4j 状态
        try:
            from core.memory.graph_manager import get_kg_manager
            kg_manager = get_kg_manager()
            stats = kg_manager.get_stats()
            st.markdown(f"**Neo4j 节点总数**: {stats.get('total_nodes', 0)}")
            st.markdown(f"**Neo4j 关系总数**: {stats.get('total_relationships', 0)}")
        except Exception as e:
            st.markdown(f"**Neo4j 状态**: 连接失败")

        # 向量存储状态
        try:
            from core.memory.vector_store import get_vector_store
            vector_store = get_vector_store()
            stats = vector_store.get_stats()
            st.markdown(f"**向量文档数**: {stats.get('total_documents', 0)}")
        except Exception as e:
            st.markdown(f"**向量存储状态**: 初始化失败")


def render_clear_conversation_button(agent) -> None:
    """
    渲染清除对话按钮

    Args:
        agent: 代理实例
    """
    if st.button("🗑️ 清除对话", type="secondary"):
        agent.reset_conversation()
        st.session_state.messages = []
        st.success("对话已清除！")
        st.rerun()


if __name__ == "__main__":
    # 测试界面组件
    print("=== 聊天界面组件测试 ===\n")
    print("✅ 所有组件已定义")
    print("请在 Streamlit 应用中查看实际效果")
