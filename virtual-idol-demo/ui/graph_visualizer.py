"""
知识图谱可视化组件
使用 Pyvis 创建交互式网络图
"""

import streamlit as st
from typing import Dict, Any, List
import networkx as nx
from pyvis.network import Network
import os
from datetime import datetime

from config.prompts import IDOL_PERSONA


# 节点类型颜色映射
NODE_COLORS = {
    "User": "#FF6B6B",        # 红色
    "Idol": "#4ECDC4",         # 青色
    "Preference": "#FFE66D",   # 黄色
    "Event": "#95E1D3",        # 绿色
    "Emotion": "#F38181",      # 粉色
    "Topic": "#AA96DA",        # 紫色
    "Location": "#FCBAD3",     # 浅粉
    "Activity": "#FFFFD2",     # 浅黄
    "Person": "#A8E6CF",       # 薄荷绿
    "Concept": "#FFD93D",      # 橙色
    "Unknown": "#CCCCCC"       # 灰色
}


def get_node_color(node_type: str) -> str:
    """获取节点颜色"""
    return NODE_COLORS.get(node_type, NODE_COLORS["Unknown"])


def create_knowledge_graph_html(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    height: str = "600px"
) -> str:
    """
    创建知识图谱的 HTML

    Args:
        nodes: 节点列表
        edges: 边列表
        height: 图表高度

    Returns:
        HTML 字符串
    """
    # 创建 NetworkX 图
    G = nx.Graph()

    # 添加节点
    for node in nodes:
        node_id = node.get("id", node.get("name", str(hash(str(node)))))
        label = node.get("label", node.get("name", "Unknown"))
        group = node.get("group", "Unknown")

        G.add_node(
            node_id,
            label=label,
            title=f"类型: {group}\n名称: {label}",
            color=get_node_color(group),
            group=group
        )

    # 添加边
    for edge in edges:
        source = edge.get("from", edge.get("source", ""))
        target = edge.get("to", edge.get("target", ""))
        label = edge.get("label", "")

        if source and target:
            G.add_edge(
                source,
                target,
                title=label,
                label=label,
                color="#888888"
            )

    # 转换为 Pyvis
    net = Network(
        height=height,
        width="100%",
        bgcolor="#1e1e1e",
        font_color="white",
        directed=False
    )

    net.from_nx(G)

    # 配置物理引擎
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {
          "enabled": true,
          "iterations": 200
        }
      },
      "nodes": {
        "font": {
          "size": 14,
          "face": "Arial"
        },
        "borderWidth": 2
      },
      "edges": {
        "width": 1,
        "smooth": {
          "type": "continuous"
        },
        "arrows": {
          "to": {
            "enabled": false
          }
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200,
        "zoomView": true,
        "dragView": true
      }
    }
    """)

    # 生成 HTML
    html_path = "knowledge_graph.html"
    net.save_graph(html_path)

    # 读取 HTML
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 清理临时文件
    if os.path.exists(html_path):
        os.remove(html_path)

    return html_content


def render_knowledge_graph(
    kg_data: Dict[str, Any],
    height: str = "600px",
    show_stats: bool = True
) -> None:
    """
    在 Streamlit 中渲染知识图谱

    Args:
        kg_data: 知识图谱数据
        height: 图表高度
        show_stats: 是否显示统计信息
    """
    nodes = kg_data.get("nodes", [])
    edges = kg_data.get("edges", [])

    # 追踪更新历史
    if "graph_update_history" not in st.session_state:
        st.session_state.graph_update_history = []

    # 记录当前状态
    current_stats = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "nodes": len(nodes),
        "edges": len(edges)
    }

    # 只在有变化时记录
    if not st.session_state.graph_update_history or \
       st.session_state.graph_update_history[-1]["nodes"] != current_stats["nodes"] or \
       st.session_state.graph_update_history[-1]["edges"] != current_stats["edges"]:
        st.session_state.graph_update_history.append(current_stats)

    if not nodes:
        st.info("🕸️ 暂无知识图谱数据，开始对话后会自动构建...")
        return

    # 显示统计信息
    if show_stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("节点数", len(nodes))
        with col2:
            st.metric("关系数", len(edges))
        with col3:
            # 计算节点类型分布
            node_types = {}
            for node in nodes:
                group = node.get("group", "Unknown")
                node_types[group] = node_types.get(group, 0) + 1

            dominant_type = max(node_types.items(), key=lambda x: x[1])[0] if node_types else "N/A"
            st.metric("主要节点类型", dominant_type)

        # 显示更新历史
        if len(st.session_state.graph_update_history) > 1:
            with st.expander("📈 图谱增长历史"):
                history_data = st.session_state.graph_update_history
                for i, record in enumerate(history_data):
                    if i == 0:
                        st.caption(f"🌱 初始: {record['nodes']} 节点, {record['edges']} 关系 ({record['timestamp']})")
                    else:
                        prev = history_data[i-1]
                        node_delta = record['nodes'] - prev['nodes']
                        edge_delta = record['edges'] - prev['edges']
                        st.caption(f"✨ 更新: {record['nodes']} 节点 ({node_delta:+d}), {record['edges']} 关系 ({edge_delta:+d}) - {record['timestamp']}")

        st.markdown("---")

    # 生成图谱 HTML
    html = create_knowledge_graph_html(nodes, edges, height=height)

    # 渲染
    st.components.v1.html(html, height=height, scrolling=True)


def render_graph_legend():
    """渲染图例"""
    st.markdown("### 📖 节点类型图例")

    legend_html = """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">
    """

    for node_type, color in NODE_COLORS.items():
        if node_type != "Unknown":
            legend_html += f"""
            <div style="display: flex; align-items: center; gap: 5px; padding: 5px 10px;
                        background-color: #2a2a2a; border-radius: 5px;">
                <div style="width: 20px; height: 20px; background-color: {color};
                           border-radius: 50%; border: 2px solid white;"></div>
                <span style="color: white; font-size: 12px;">{node_type}</span>
            </div>
            """

    legend_html += "</div>"

    st.markdown(legend_html, unsafe_allow_html=True)


def render_empty_graph_placeholder():
    """渲染空图谱占位符"""
    st.markdown("""
    ### 🕸️ 知识图谱可视化

    当你开始与偶像对话后，这里会自动显示：
    - **节点**: 对话中提到的人物、地点、偏好、事件等
    - **关系**: 它们之间的联系（喜欢、提到、导致等）
    - **交互**: 可以拖拽节点、缩放视图、悬停查看详情

    开始对话吧！✨
    """)


if __name__ == "__main__":
    # 测试图谱可视化
    print("=== 知识图谱可视化测试 ===\n")

    # 模拟数据
    test_nodes = [
        {"id": "1", "label": "用户", "group": "User"},
        {"id": "2", "label": "星野光", "group": "Idol"},
        {"id": "3", "label": "摇滚音乐", "group": "Preference"},
        {"id": "4", "label": "重金属", "group": "Topic"},
    ]

    test_edges = [
        {"from": "1", "to": "2", "label": "喜欢"},
        {"from": "1", "to": "3", "label": "LIKES"},
        {"from": "3", "to": "4", "label": "RELATED_TO"},
    ]

    test_data = {
        "nodes": test_nodes,
        "edges": test_edges
    }

    # 生成 HTML
    html = create_knowledge_graph_html(test_nodes, test_edges)

    # 保存到文件查看
    with open("test_graph.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ 测试图谱已生成: test_graph.html")
    print("可以在浏览器中打开查看")
