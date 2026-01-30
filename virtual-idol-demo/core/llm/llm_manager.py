"""
LLM 管理器
支持多个 LLM 提供商（OpenAI, Anthropic, DeepSeek）
"""

from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config.settings import settings


class LLMManager:
    """LLM 管理器类"""

    def __init__(self, provider: Optional[str] = None):
        """
        初始化 LLM 管理器

        Args:
            provider: LLM 提供商（openai, anthropic, deepseek），None 则自动选择
        """
        self.provider = provider or settings.LLM_PROVIDER
        self.llm_config = settings.get_llm_config()
        self.llm = self._create_llm()
        self.parser = StrOutputParser()

    def _create_llm(self):
        """创建 LLM 实例"""
        provider = self.llm_config["provider"]

        if provider == "openai":
            return ChatOpenAI(
                model=self.llm_config["model"],
                api_key=self.llm_config["api_key"],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                streaming=True
            )
        elif provider == "anthropic":
            return ChatAnthropic(
                model=self.llm_config["model"],
                api_key=self.llm_config["api_key"],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                streaming=True
            )
        elif provider == "deepseek":
            # DeepSeek 使用 OpenAI 兼容 API
            return ChatOpenAI(
                base_url="https://api.deepseek.com",
                model=self.llm_config["model"],
                api_key=self.llm_config["api_key"],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                streaming=True
            )
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 其他参数

        Returns:
            生成的响应文本
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=prompt))

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            raise Exception(f"LLM 生成失败: {str(e)}")

    def generate_with_history(
        self,
        prompt: str,
        chat_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        基于历史对话生成响应

        Args:
            prompt: 当前用户输入
            chat_history: 历史对话列表 [{"role": "user/assistant", "content": "..."}]
            system_prompt: 系统提示
            **kwargs: 其他参数

        Returns:
            生成的响应文本
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        # 添加历史对话
        for msg in chat_history[-settings.MAX_HISTORY_LENGTH:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # 添加当前输入
        messages.append(HumanMessage(content=prompt))

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            raise Exception(f"LLM 生成失败: {str(e)}")

    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        流式生成响应

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 其他参数

        Yields:
            响应文本片段
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=prompt))

        try:
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                elif isinstance(chunk, str):
                    yield chunk
        except Exception as e:
            yield f"错误: {str(e)}"

    def stream_with_history(
        self,
        prompt: str,
        chat_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        基于历史对话流式生成响应

        Args:
            prompt: 当前用户输入
            chat_history: 历史对话列表
            system_prompt: 系统提示
            **kwargs: 其他参数

        Yields:
            响应文本片段
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        # 添加历史对话
        for msg in chat_history[-settings.MAX_HISTORY_LENGTH:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # 添加当前输入
        messages.append(HumanMessage(content=prompt))

        try:
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                elif isinstance(chunk, str):
                    yield chunk
        except Exception as e:
            yield f"错误: {str(e)}"

    def extract_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        提取结构化 JSON 数据

        Args:
            prompt: 提示词（要求输出 JSON）
            **kwargs: 其他参数

        Returns:
            解析后的 JSON 字典
        """
        import json

        response = self.generate(prompt, **kwargs)

        # 尝试提取 JSON
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取代码块中的 JSON
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                return json.loads(response[start:end].strip())
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                return json.loads(response[start:end].strip())
            else:
                # 尝试提取 { } 之间的内容
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end != -1:
                    return json.loads(response[start:end])
                else:
                    raise ValueError(f"无法从响应中提取 JSON: {response}")

    def get_provider_info(self) -> Dict[str, Any]:
        """获取当前提供商信息"""
        return {
            "provider": self.llm_config["provider"],
            "model": self.llm_config["model"],
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS
        }


# 全局 LLM 管理器实例
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """获取全局 LLM 管理器实例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager


if __name__ == "__main__":
    # 测试 LLM 管理器
    print("=== LLM 管理器测试 ===\n")

    try:
        llm_manager = get_llm_manager()
        print(f"✅ LLM 管理器初始化成功")
        print(f"提供商: {llm_manager.get_provider_info()}\n")

        # 测试简单生成
        print("测试 1: 简单生成")
        response = llm_manager.generate("用一句话介绍你自己")
        print(f"响应: {response}\n")

        # 测试流式生成
        print("测试 2: 流式生成")
        print("响应: ", end="")
        for chunk in llm_manager.stream("说'你好，世界！'"):
            print(chunk, end="", flush=True)
        print("\n")

        # 测试带历史生成
        print("测试 3: 带历史对话生成")
        history = [
            {"role": "user", "content": "你好！"},
            {"role": "assistant", "content": "你好呀！很高兴见到你~"}
        ]
        response = llm_manager.generate_with_history(
            "我叫什么名字？",
            chat_history=history
        )
        print(f"响应: {response}\n")

        print("✅ 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        print("提示：请确保在 .env 文件中配置了正确的 API keys")
