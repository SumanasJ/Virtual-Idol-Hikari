# 🚀 GitHub 上传指南

## 📋 当前状态

✅ Git 仓库已初始化
✅ 所有文件已提交
⏳ 待上传到 GitHub

---

## 🎯 方式 1: 网页创建（推荐）

### 步骤 1: 创建 GitHub 私有仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `virtual-idol-demo`
   - **Description**: `AI 虚拟偶像 Demo - 基于 Agentic RAG 和知识图谱`
   - **Visibility**: 🔒 **Private**（私有）
   - ❌ 不要勾选 "Add a README"
   - ❌ 不要勾选 "Add .gitignore"

3. 点击 **Create repository**

### 步骤 2: 推送代码

创建后，GitHub 会显示命令。在终端执行：

```bash
cd virtual-idol-demo
git remote add origin https://github.com/你的用户名/virtual-idol-demo.git
git branch -M main
git push -u origin main
```

**注意**: 把 `你的用户名` 替换成你的 GitHub 用户名。

---

## ⚡ 方式 2: GitHub CLI（最快）

### 安装 GitHub CLI

**Mac**:
```bash
brew install gh
```

### 认证
```bash
gh auth login
```

### 一键创建并推送
```bash
cd virtual-idol-demo
gh repo create virtual-idol-demo --private --source=. --remote=origin --push
```

完成！✨

---

## 🔐 安全提醒

⚠️ `.env` 文件**不会**被上传（已在 .gitignore 中）
- ✅ `.env.example` 会作为模板上传
- ✅ API Keys 安全，不会被泄露
- ⚠️ 在另一台电脑需要重新配置 `.env`

---

## 📥 在另一台电脑克隆

```bash
git clone https://github.com/你的用户名/virtual-idol-demo.git
cd virtual-idol-demo
cp .env.example .env
# 编辑 .env 填入配置
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## ✅ 选择哪种方式？

- **方式 1**（网页）：不想安装工具，手动操作
- **方式 2**（CLI）：最快，一键搞定

推荐使用方式 2（GitHub CLI），非常方便！😊
