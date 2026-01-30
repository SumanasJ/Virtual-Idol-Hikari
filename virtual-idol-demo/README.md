# AI 虚拟偶像 Demo

基于 LangGraph、知识图谱和 RAG 技术的智能虚拟偶像对话系统。

## 功能特性

- 🧠 **长时记忆**: 自动从对话中抽取实体和关系，构建知识图谱
- 💬 **实时对话**: 流畅的实时互动体验
- 🎭 **养成式互动**: 用户对话影响偶像性格和响应风格
- 🕸️ **可视化展示**: 实时展示知识图谱和对话关系网络

## 技术栈

- **代理框架**: LangGraph + LangChain
- **知识图谱**: Neo4j AuraDB
- **向量检索**: Chroma
- **前端界面**: Streamlit + Pyvis
- **LLM**: GPT-4o / Claude 3.5 / DeepSeek-R2

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API keys
# - OPENAI_API_KEY 或 ANTHROPIC_API_KEY
# - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
```

### 3. 注册 Neo4j AuraDB（免费）

1. 访问 https://neo4j.com/cloud/aura/
2. 注册免费账户
3. 创建一个新的数据库实例
4. 复制连接信息到 `.env` 文件

### 4. 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中打开 http://localhost:8501

## 项目结构

```
virtual-idol-demo/
├── app.py                      # Streamlit 主应用
├── core/
│   ├── agent/                 # LangGraph 代理
│   ├── memory/                # 知识图谱和向量存储
│   ├── personality/           # 性格养成系统
│   └── llm/                   # LLM 调用管理
├── tools/                     # 检索工具
├── config/                    # 配置和提示词
├── ui/                        # 界面组件
└── data/                      # 示例数据
```

## 核心功能演示

### 长时记忆

```
用户: 我喜欢听摇滚音乐
偶像: 真的吗？我也很喜欢摇滚！最喜欢哪种风格？
用户: 重金属
偶像: 重金属超有力量感的！
...
用户: 你还记得我喜欢什么音乐吗？
偶像: 当然记得！你喜欢重金属摇滚~
```

### 性格养成

偶像的性格会根据对话动态调整：
- **开朗度**: 根据对话氛围变化
- **温柔度**: 根据用户情绪调整
- **同理心**: 根据用户反馈提升

### 知识图谱可视化

右侧面板实时展示：
- 实体节点（用户、偏好、事件等）
- 关系边（喜欢、提到、导致等）
- 交互式网络图

## 配置说明

### 性格设置

编辑 `config/prompts.py` 中的 `IDOL_PERSONA` 来自定义偶像：

```python
IDOL_PERSONA = {
    "name": "星野光",
    "age": 17,
    "base_personality": {
        "cheerfulness": 0.8,
        "gentleness": 0.6,
        "energy": 0.9,
        "curiosity": 0.7,
        "empathy": 0.5
    },
    "background": "出生于大阪的17岁虚拟偶像...",
    "speaking_style": "大阪腔，元气满满"
}
```

### 实体抽取 Schema

在 `core/memory/graph_manager.py` 中自定义节点和关系类型：

```python
allowed_nodes = ["User", "Idol", "Preference", "Event", "Emotion", "Topic"]
allowed_relationships = ["LIKES", "MENTIONS", "CAUSES", "EXPRESSES", "DISCUSSES"]
```

## 测试场景

### 场景 1: 偏好记忆
验证偶像能否记住用户之前提到的偏好

### 场景 2: 性格养成
验证性格参数随对话合理变化

### 场景 3: 事件推理
验证知识图谱正确更新和查询

## 开发路线

- [x] Phase 1: 基础设施搭建
- [ ] Phase 2: LangGraph 代理实现
- [ ] Phase 3: 性格系统实现
- [ ] Phase 4: Streamlit 界面开发
- [ ] Phase 5: 优化和完善

## 常见问题

**Q: 响应很慢怎么办？**
A: 可以调整 `K_RETRIEVAL` 参数减少检索数量，或使用更快的 LLM。

**Q: Neo4j 免费层有存储限制？**
A: 定期清理不重要的节点，或考虑使用本地 Memgraph。

**Q: 如何添加新的 LLM？**
A: 在 `core/llm/llm_manager.py` 中添加新的 provider。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 参考资料

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Neo4j LLM Knowledge Graph Builder](https://neo4j.com/developer/llm-knowledge-graph-builder/)
- [Microsoft GraphRAG](https://github.com/microsoft/graphrag)
- [Streamlit 聊天教程](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
