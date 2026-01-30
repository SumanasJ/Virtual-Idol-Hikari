@echo off
REM AI 虚拟偶像 Demo - Windows 快速启动脚本

echo ==================================
echo 🎭 AI 虚拟偶像 Demo - 快速启动
echo ==================================
echo.

REM 检查 Python 版本
echo 1️⃣ 检查 Python 版本...
python --version
if errorlevel 1 (
    echo    ❌ Python 未安装或不在 PATH 中
    echo    请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查是否存在虚拟环境
if not exist "venv" (
    echo.
    echo 2️⃣ 创建虚拟环境...
    python -m venv venv
    echo    ✅ 虚拟环境创建成功
) else (
    echo 2️⃣ 虚拟环境已存在，跳过创建
)

REM 激活虚拟环境
echo.
echo 3️⃣ 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级 pip
echo.
echo 4️⃣ 升级 pip...
python -m pip install --upgrade pip -q

REM 安装依赖
echo.
echo 5️⃣ 安装依赖包...
pip install -r requirements.txt

REM 检查 .env 文件
echo.
echo 6️⃣ 检查配置文件...
if not exist ".env" (
    echo    ⚠️  .env 文件不存在，从模板复制...
    copy .env.example .env
    echo.
    echo    ❗ 请编辑 .env 文件，填入以下信息：
    echo       - OPENAI_API_KEY 或其他 LLM API Key
    echo       - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
    echo.
    pause
) else (
    echo    ✅ .env 文件已存在
)

REM 验证配置
echo.
echo 7️⃣ 验证配置...
python -c "from config.settings import settings; settings.validate()"
if errorlevel 1 (
    echo.
    echo    ❌ 配置验证失败！请检查 .env 文件
    pause
    exit /b 1
)

echo.
echo ==================================
echo ✅ 所有检查通过！
echo ==================================
echo.
echo 启动应用...
echo.

REM 启动 Streamlit
streamlit run app.py
