"""
配置管理模块
加载和管理所有系统配置
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """系统配置类"""

    # LLM 配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

    # 选择的 LLM 提供商（openai, anthropic, deepseek）
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")

    # 模型配置
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1000"))

    # Neo4j 配置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

    # Chroma 配置
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # 应用配置
    APP_TITLE: str = os.getenv("APP_TITLE", "AI 虚拟偶像 Demo")
    MAX_HISTORY_LENGTH: int = int(os.getenv("MAX_HISTORY_LENGTH", "20"))
    K_RETRIEVAL: int = int(os.getenv("K_RETRIEVAL", "3"))

    # 会话配置
    SESSION_ID: str = os.getenv("SESSION_ID", "default")

    # 性格进化配置
    EVOLUTION_RATE: float = float(os.getenv("EVOLUTION_RATE", "0.05"))
    MAX_PERSONALITY_DRIFT: float = float(os.getenv("MAX_PERSONALITY_DRIFT", "0.2"))

    # 知识图谱配置
    ALLOWED_NODES: list = [
        "User", "Idol", "Preference", "Event", "Emotion", "Topic",
        "Location", "Activity", "Person", "Concept"
    ]

    ALLOWED_RELATIONSHIPS: list = [
        "LIKES", "DISLIKES", "MENTIONS", "DISCUSSES",
        "CAUSES", "EXPRESSES", "PARTICIPATES_IN",
        "LOCATED_IN", "RELATED_TO", "WANTS_TO_DO",
        "DID", "PLANNED_TO", "FEELS_ABOUT"
    ]

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """验证配置是否完整"""
        errors = []
        warnings = []

        # 检查 LLM API Key
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY and not cls.DEEPSEEK_API_KEY:
            errors.append(
                "至少需要一个 LLM API Key (OPENAI_API_KEY, ANTHROPIC_API_KEY, 或 DEEPSEEK_API_KEY)"
            )

        # 检查 Neo4j 配置
        if not cls.NEO4J_URI:
            errors.append("NEO4J_URI 未配置")
        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD 未配置")

        # 警告
        if cls.EVOLUTION_RATE > 0.1:
            warnings.append(
                f"EVOLUTION_RATE ({cls.EVOLUTION_RATE}) 较高，可能导致性格变化过快"
            )

        return {
            "errors": errors,
            "warnings": warnings,
            "valid": len(errors) == 0
        }

    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """获取 LLM 配置"""
        if cls.LLM_PROVIDER == "openai":
            return {
                "provider": "openai",
                "model": cls.MODEL_NAME,
                "api_key": cls.OPENAI_API_KEY,
                "temperature": cls.TEMPERATURE,
                "max_tokens": cls.MAX_TOKENS
            }
        elif cls.LLM_PROVIDER == "anthropic":
            return {
                "provider": "anthropic",
                "model": cls.MODEL_NAME if "claude" in cls.MODEL_NAME.lower() else "claude-3-5-sonnet-20241022",
                "api_key": cls.ANTHROPIC_API_KEY,
                "temperature": cls.TEMPERATURE,
                "max_tokens": cls.MAX_TOKENS
            }
        elif cls.LLM_PROVIDER == "deepseek":
            return {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "api_key": cls.DEEPSEEK_API_KEY,
                "temperature": cls.TEMPERATURE,
                "max_tokens": cls.MAX_TOKENS
            }
        else:
            # 默认使用第一个可用的
            if cls.OPENAI_API_KEY:
                cls.LLM_PROVIDER = "openai"
                return cls.get_llm_config()
            elif cls.ANTHROPIC_API_KEY:
                cls.LLM_PROVIDER = "anthropic"
                return cls.get_llm_config()
            elif cls.DEEPSEEK_API_KEY:
                cls.LLM_PROVIDER = "deepseek"
                return cls.get_llm_config()
            else:
                raise ValueError("没有可用的 LLM API Key")

    @classmethod
    def get_neo4j_config(cls) -> Dict[str, str]:
        """获取 Neo4j 配置"""
        return {
            "uri": cls.NEO4J_URI,
            "user": cls.NEO4J_USER,
            "password": cls.NEO4J_PASSWORD
        }

    @classmethod
    def display(cls) -> None:
        """显示当前配置（隐藏敏感信息）"""
        print(f"\n{'='*50}")
        print(f"🎭 {cls.APP_TITLE} - 配置信息")
        print(f"{'='*50}\n")

        print("📝 LLM 配置:")
        print(f"  Provider: {cls.LLM_PROVIDER}")
        print(f"  Model: {cls.MODEL_NAME}")
        print(f"  Temperature: {cls.TEMPERATURE}")
        print(f"  API Key: {'{' + cls.OPENAI_API_KEY[:8] + '...' if cls.OPENAI_API_KEY else 'Not set'}")

        print("\n🗄️  Neo4j 配置:")
        print(f"  URI: {cls.NEO4J_URI[:30] + '...' if cls.NEO4J_URI else 'Not set'}")
        print(f"  User: {cls.NEO4J_USER}")

        print("\n💾 向量存储:")
        print(f"  目录: {cls.CHROMA_PERSIST_DIR}")
        print(f"  模型: {cls.EMBEDDING_MODEL}")

        print("\n⚙️  应用配置:")
        print(f"  最大历史长度: {cls.MAX_HISTORY_LENGTH}")
        print(f"  检索数量 (K): {cls.K_RETRIEVAL}")
        print(f"  性格进化率: {cls.EVOLUTION_RATE}")

        print("\n🕸️  知识图谱:")
        print(f"  节点类型: {', '.join(cls.ALLOWED_NODES[:5])}...")
        print(f"  关系类型: {', '.join(cls.ALLOWED_RELATIONSHIPS[:5])}...")

        print(f"\n{'='*50}\n")


# 全局设置实例
settings = Settings()


if __name__ == "__main__":
    # 测试配置
    settings.display()

    # 验证配置
    validation = settings.validate()
    if validation["valid"]:
        print("✅ 配置验证通过！")
    else:
        print("❌ 配置错误:")
        for error in validation["errors"]:
            print(f"  - {error}")

    if validation["warnings"]:
        print("⚠️  警告:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
