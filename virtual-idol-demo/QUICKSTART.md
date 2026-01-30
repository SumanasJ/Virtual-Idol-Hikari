# 快速开始指南

## 5 分钟启动 AI 虚拟偶像 Demo

### 前置要求

- Python 3.8 或更高版本
- pip 包管理器
- OpenAI API Key（或其他 LLM API Key）
- Neo4j AuraDB 免费账户

### 步骤 1: 克隆项目（如果从 GitHub）

```bash
git clone <repository-url>
cd virtual-idol-demo
```

### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入以下信息：
# - OPENAI_API_KEY=sk-xxx（或 ANTHROPIC_API_KEY / DEEPSEEK_API_KEY）
# - NEO4J_URI=bolt://xxx.databases.neo4j.io:7687
# - NEO4J_USER=neo4j
# - NEO4J_PASSWORD=your-password
```

**获取 Neo4j AuraDB 免费账户：**
1. 访问 https://neo4j.com/cloud/aura/
2. 注册免费账户
3. 创建一个新的数据库实例
4. 复制连接信息到 `.env` 文件

### 步骤 3: 安装依赖

#### Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows:
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 步骤 4: 测试系统（可选）

```bash
python test_system.py
```

这将测试所有组件是否正常工作。

### 步骤 5: 启动应用

```bash
streamlit run app.py
```

应用将在浏览器中打开：http://localhost:8501

## 快速测试对话

启动后，可以尝试以下对话：

1. **基础介绍**
   - 你: "介绍一下你自己吧！"
   - 偶像: 会自我介绍，展示她的人格设定

2. **偏好记忆**
   - 你: "我喜欢听重金属音乐"
   - 偶像: 会记住这个偏好
   - （几轮对话后）
   - 你: "你还记得我喜欢什么音乐吗？"
   - 偶像: 应该能正确回答"重金属"

3. **情感互动**
   - 你: "我最近心情不太好..."
   - 偶像: 会表现出同理心，温柔安慰你
   - 观察右侧的"同理心"和"温柔度"指标上升

4. **知识图谱可视化**
   - 多聊几句后，查看右侧的"知识图谱"标签
   - 可以看到自动抽取的实体和关系
   - 节点可以拖拽、缩放、悬停查看详情

## 故障排查

### 问题 1: "配置验证失败"
**解决方法**: 检查 `.env` 文件是否正确配置
- 确保 OPENAI_API_KEY 或其他 LLM API Key 已填入
- 确保 Neo4j URI、用户名、密码正确

### 问题 2: "Neo4j 连接失败"
**解决方法**:
1. 确认 Neo4j AuraDB 实例正在运行
2. 检查网络连接
3. 验证 URI 格式：`bolt://xxx.databases.neo4j.io:7687`

### 问题 3: "响应很慢"
**解决方法**:
1. 检查网络连接速度
2. 调整 `.env` 中的 `K_RETRIEVAL` 参数（减少检索数量）
3. 考虑使用更快的 LLM 模型

### 问题 4: "知识图谱没有显示"
**解决方法**:
1. 先进行几轮对话
2. 刷新页面
3. 检查 Neo4j 数据库是否有数据

## 下一步

- 查看 [README.md](README.md) 了解更多功能
- 自定义 `config/prompts.py` 中的偶像人设
- 调整 `config/settings.py` 中的系统参数
- 查看知识图谱数据在 Neo4j 浏览器中的可视化

## 获取帮助

如遇问题：
1. 查看终端的错误日志
2. 运行 `python test_system.py` 诊断问题
3. 检查 Neo4j 控制台是否有错误
4. 查看 README.md 中的"常见问题"章节
