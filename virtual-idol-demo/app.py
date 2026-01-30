"""
AI 虚拟偶像 Demo 主应用
基于 LangGraph、知识图谱和 RAG 技术的智能对话系统
"""

import streamlit as st
from typing import Dict, Any
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 页面配置
st.set_page_config(
    page_title="AI 虚拟偶像 Demo",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入模块
from config.settings import settings
from config.prompts import IDOL_PERSONA
from core.agent.langgraph_agent import get_agent
from ui.chat_interface import (
    render_chat_history,
    render_personality_panel,
    render_session_stats,
    render_idol_profile,
    render_suggested_questions,
    render_system_info,
    render_clear_conversation_button
)
from ui.graph_visualizer import (
    render_knowledge_graph,
    render_graph_legend,
    render_empty_graph_placeholder
)


def init_session_state():
    """初始化会话状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "agent" not in st.session_state:
        st.session_state.agent = get_agent()

    if "page" not in st.session_state:
        st.session_state.page = "chat"


def validate_configuration():
    """验证配置"""
    validation = settings.validate()

    if not validation["valid"]:
        st.error("❌ 配置错误，请检查 .env 文件：")
        for error in validation["errors"]:
            st.markdown(f"- {error}")
        st.stop()

    if validation["warnings"]:
        st.warning("⚠️ 配置警告：")
        for warning in validation["warnings"]:
            st.markdown(f"- {warning}")


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown(f"# 🎭 {IDOL_PERSONA['name']}")

        # 标签页
        tab1, tab2, tab3, tab4 = st.tabs(["📊 性格", "🌟 资料", "📈 统计", "⚙️ 系统"])

        with tab1:
            personality = st.session_state.agent.get_personality()
            render_personality_panel(personality)

        with tab2:
            render_idol_profile()

        with tab3:
            render_session_stats(st.session_state.agent)

        with tab4:
            render_system_info()

        st.markdown("---")

        # 操作按钮
        render_clear_conversation_button(st.session_state.agent)

        # 建议问题
        st.markdown("---")
        render_suggested_questions()


def render_main_interface():
    """渲染主界面"""
    # 创建两栏布局
    col_chat, col_graph = st.columns([3, 2])

    with col_chat:
        st.markdown("## 💬 对话")

        # 渲染聊天历史
        render_chat_history(st.session_state.messages)

        # 聊天输入
        if prompt := st.chat_input(f"和 {IDOL_PERSONA['name']} 聊天吧~"):
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})

            # 显示用户消息
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            # 生成助手回复
            with st.chat_message("assistant", avatar="🎭"):
                with st.spinner("思考中..."):
                    response = st.session_state.agent.chat(prompt)

                st.markdown(response)

            # 添加助手消息到历史
            st.session_state.messages.append({"role": "assistant", "content": response})

    with col_graph:
        st.markdown("## 🕸️ 知识图谱")

        # 标签页
        tab_graph, tab_legend = st.tabs(["📊 图谱", "📖 图例"])

        with tab_graph:
            # 获取知识图谱数据
            kg_data = st.session_state.agent.get_kg_data()

            if kg_data.get("nodes"):
                # 显示图谱
                render_knowledge_graph(kg_data, height="500px")
            else:
                # 显示占位符
                render_empty_graph_placeholder()

        with tab_legend:
            render_graph_legend()


def render_header():
    """渲染页面头部"""
    st.title(f"🎭 AI 虚拟偶像 Demo - {IDOL_PERSONA['name']}")
    st.markdown(f"**{IDOL_PERSONA['background']}**")
    st.markdown("---")


def main():
    """主函数"""
    # 初始化会话状态
    init_session_state()

    # 验证配置
    validate_configuration()

    # 渲染头部
    render_header()

    # 渲染侧边栏
    render_sidebar()

    # 渲染主界面
    render_main_interface()

    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>🎭 AI 虚拟偶像 Demo | 基于 LangGraph + Neo4j + Chroma 构建</p>
        <p style='font-size: 12px;'>
        <a href='https://github.com' target='_blank'>GitHub</a> |
        <a href='https://langchain-ai.github.io/langgraph/' target='_blank'>LangGraph</a> |
        <a href='https://neo4j.com/' target='_blank'>Neo4j</a>
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ 应用启动失败: {str(e)}")
        st.markdown("### 常见问题")

        with st.expander("📋 配置检查清单"):
            st.markdown("""
            1. **LLM API Key**
               - 检查 `.env` 文件中是否配置了 `OPENAI_API_KEY` 或其他 LLM API Key

            2. **Neo4j 数据库**
               - 确保已注册 Neo4j AuraDB 免费账户
               - 检查 `.env` 文件中的 Neo4j 连接信息是否正确

            3. **Python 依赖**
               - 运行 `pip install -r requirements.txt` 安装所有依赖

            4. **网络连接**
               - 确保能够访问 LLM API 和 Neo4j 数据库
            """)

        with st.expander("🔧 获取帮助"):
            st.markdown("""
            如果遇到问题，请检查：
            1. `.env` 文件是否在项目根目录
            2. API keys 是否正确且有效
            3. Neo4j 数据库是否在线
            4. 是否有足够的网络带宽

            详细信息请参考 [README.md](README.md)
            """)

        # 显示错误详情
        with st.expander("❌ 错误详情"):
            import traceback
            st.code(traceback.format_exc())
