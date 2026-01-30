#!/bin/bash

# AI 虚拟偶像 Demo - 快速启动脚本

set -e

echo "=================================="
echo "🎭 AI 虚拟偶像 Demo - 快速启动"
echo "=================================="
echo ""

# 检查 Python 版本
echo "1️⃣ 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   当前版本: $python_version"

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "2️⃣ 创建虚拟环境..."
    python3 -m venv venv
    echo "   ✅ 虚拟环境创建成功"
else
    echo "2️⃣ 虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo ""
echo "3️⃣ 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo ""
echo "4️⃣ 升级 pip..."
pip install --upgrade pip -q

# 安装依赖
echo ""
echo "5️⃣ 安装依赖包..."
pip install -r requirements.txt

# 检查 .env 文件
echo ""
echo "6️⃣ 检查配置文件..."
if [ ! -f ".env" ]; then
    echo "   ⚠️  .env 文件不存在，从模板复制..."
    cp .env.example .env
    echo ""
    echo "   ❗ 请编辑 .env 文件，填入以下信息："
    echo "      - OPENAI_API_KEY 或其他 LLM API Key"
    echo "      - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD"
    echo ""
    read -p "   编辑完成后按 Enter 继续..."
else
    echo "   ✅ .env 文件已存在"
fi

# 验证配置
echo ""
echo "7️⃣ 验证配置..."
python3 -c "from config.settings import settings; settings.validate()"
if [ $? -ne 0 ]; then
    echo ""
    echo "   ❌ 配置验证失败！请检查 .env 文件"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ 所有检查通过！"
echo "=================================="
echo ""
echo "启动应用..."
echo ""

# 启动 Streamlit
streamlit run app.py
