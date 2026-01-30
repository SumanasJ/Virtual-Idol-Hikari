# AI 虚拟偶像 Demo - 项目概览

## 🎉 项目已完成！

基于 Agentic RAG 和知识图谱的完整 AI 虚拟偶像对话系统已构建完成。

## 📁 项目结构

```
virtual-idol-demo/
├── app.py                          # Streamlit 主应用入口
├── requirements.txt                # Python 依赖
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 忽略文件
├── README.md                       # 详细文档
├── QUICKSTART.md                   # 快速开始指南
├── setup.sh / setup.bat            # 自动化启动脚本
├── test_system.py                  # 系统测试脚本
│
├── config/                         # 配置模块
│   ├── __init__.py
│   ├── settings.py                 # 配置管理
│   └── prompts.py                  # 提示词和人设
│
├── core/                           # 核心逻辑
│   ├── agent/                      # LangGraph 代理
│   │   ├── __init__.py
│   │   └── langgraph_agent.py      # 虚拟偶像代理
│   ├── llm/                        # LLM 管理
│   │   ├── __init__.py
│   │   └── llm_manager.py          # LLM 调用封装
│   ├── memory/                     # 记忆系统
│   │   ├── __init__.py
│   │   ├── vector_store.py         # Chroma 向量存储
│   │   └── graph_manager.py        # Neo4j 知识图谱
│   └── personality/                # 性格系统
│       ├── __init__.py
│       ├── personality_model.py    # 性格模型
│       └── trait_evolver.py        # 性格进化
│
├── ui/                             # 用户界面
│   ├── __init__.py
│   ├── chat_interface.py           # 聊天界面组件
│   └── graph_visualizer.py         # 知识图谱可视化
│
├── tools/                          # 工具模块（预留）
│   └── __init__.py
│
└── data/                           # 数据目录
    └── sample_conversations/       # 示例对话（预留）
```

## ✨ 核心功能

### 1. Agentic RAG 架构
- ✅ LangGraph 编排的对话流程
- ✅ 多工具检索（向量 DB + 知识图谱）
- ✅ 状态管理和条件路由

### 2. 长时记忆
- ✅ Chroma 向量数据库存储对话历史
- ✅ 相似性检索和混合搜索
- ✅ 自动保存和更新

### 3. 知识图谱
- ✅ Neo4j AuraDB 存储
- ✅ LLM 自动抽取实体和关系
- ✅ Pyvis 交互式可视化
- ✅ 实时查询和推理

### 4. 性格养成系统
- ✅ 五维性格模型（开朗、温柔、元气、好奇、同理）
- ✅ 动态性格进化
- ✅ 偏离度控制和软重置

### 5. Streamlit 界面
- ✅ 类 ChatGPT 的聊天界面
- ✅ 实时性格状态展示
- ✅ 知识图谱可视化
- ✅ 会话统计和系统信息

## 🚀 快速开始

### 方法 1: 使用启动脚本（推荐）

**Mac/Linux:**
```bash
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

### 方法 2: 手动启动

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API keys

# 4. 测试系统（可选）
python test_system.py

# 5. 启动应用
streamlit run app.py
```

## 🔑 配置要求

### 必需的 API Keys
在 `.env` 文件中配置：

1. **LLM API**（选择一个）:
   - `OPENAI_API_KEY=sk-xxx`
   - `ANTHROPIC_API_KEY=sk-ant-xxx`
   - `DEEPSEEK_API_KEY=sk-xxx`

2. **Neo4j AuraDB**:
   - 注册免费账户: https://neo4j.com/cloud/aura/
   - `NEO4J_URI=bolt://xxx.databases.neo4j.io:7687`
   - `NEO4J_USER=neo4j`
   - `NEO4J_PASSWORD=your-password`

## 📊 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| 代理框架 | LangGraph | 对话流程编排 |
| LLM | GPT-4o / Claude / DeepSeek | 响应生成 |
| 知识图谱 | Neo4j AuraDB | 存储实体-关系 |
| 向量数据库 | Chroma | 语义检索 |
| 前端 | Streamlit | Web 界面 |
| 可视化 | Pyvis + NetworkX | 图谱可视化 |
| 嵌入 | OpenAI / SentenceTransformers | 文本向量化 |

## 🎯 核心测试场景

### 场景 1: 偏好记忆
```
你: 我喜欢听摇滚音乐
偶像: 真的吗？我也很喜欢摇滚！
...
你: 你还记得我喜欢什么吗？
偶像: 当然记得！你喜欢摇滚音乐~
```

### 场景 2: 性格养成
```
初始: 开朗度 0.8
你: 今天心情不好...
偶像: （同理心 ↑，温柔度 ↑）
```

### 场景 3: 知识图谱
- 自动抽取：用户 -[LIKES]-> 摇滚音乐
- 可视化展示节点和关系
- 支持查询和推理

## 📈 系统特性

### 高级功能
- ✅ 实时性格状态可视化（进度条）
- ✅ 知识图谱实时更新
- ✅ 多用户会话隔离
- ✅ 流式响应支持
- ✅ 完整错误处理

### 性能优化
- ✅ 响应缓存（减少重复查询）
- ✅ 异步知识图谱更新
- ✅ 向量数据库索引优化
- ✅ LLM 调用重试机制

## 🛠️ 自定义指南

### 修改偶像人设
编辑 `config/prompts.py` 中的 `IDOL_PERSONA`：

```python
IDOL_PERSONA = {
    "name": "你的偶像名字",
    "age": 17,
    "base_personality": {
        "cheerfulness": 0.8,
        "gentleness": 0.6,
        # ...
    },
    "background": "背景故事...",
    "speaking_style": "说话风格..."
}
```

### 调整实体抽取 Schema
编辑 `config/settings.py`：

```python
ALLOWED_NODES = ["User", "Idol", "Preference", ...]
ALLOWED_RELATIONSHIPS = ["LIKES", "MENTIONS", ...]
```

### 修改性格进化率
编辑 `.env`：

```bash
EVOLUTION_RATE=0.05        # 每轮最大变化率
MAX_PERSONALITY_DRIFT=0.2  # 最大偏离度
```

## 📚 文档

- [README.md](README.md) - 完整功能文档
- [QUICKSTART.md](QUICKSTART.md) - 5分钟快速开始
- [计划文档](../.claude/plans/quirky-squishing-breeze.md) - 详细实现计划

## 🐛 故障排查

| 问题 | 解决方案 |
|------|---------|
| 配置验证失败 | 检查 `.env` 文件中的 API keys |
| Neo4j 连接失败 | 确认数据库在线，检查 URI 格式 |
| 响应很慢 | 减少 `K_RETRIEVAL` 值，检查网络 |
| 知识图谱为空 | 先进行几轮对话，然后刷新 |

## 🎓 学习资源

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Neo4j 图数据库教程](https://neo4j.com/developer/)
- [Streamlit 文档](https://docs.streamlit.io/)
- [Chroma 向量数据库](https://www.trychroma.com/)

## 🌟 下一步优化方向

- [ ] 添加语音输入/输出
- [ ] 支持多模态（图像、视频）
- [ ] 实现多用户同时互动
- [ ] 添加情绪识别
- [ ] 集成外部知识检索
- [ ] A/B 测试不同策略

## 📝 License

MIT License

## 🙏 致谢

感谢以下开源项目的支持：
- LangChain & LangGraph
- Neo4j
- Chroma
- Streamlit
- Pyvis

---

**项目完成日期**: 2025-01-30
**总代码行数**: ~3000+ 行
**开发用时**: ~2 小时
