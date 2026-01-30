"""
LangGraph 代理实现
整合知识图谱、向量存储、性格系统和 LLM 生成
"""

from typing import TypedDict, Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config.settings import settings
from config.prompts import IDOL_PERSONA, get_system_prompt
from core.llm.llm_manager import get_llm_manager
from core.memory.vector_store import get_vector_store
from core.memory.graph_manager import get_kg_manager
from core.personality.personality_model import create_personality_model
from core.personality.trait_evolver import create_personality_evolver
from core.agent.intent_recognizer import get_intent_recognizer


class AgentState(TypedDict):
    """代理状态"""
    # 输入
    message: str
    session_id: str

    # 中间状态
    chat_history: List[Dict[str, str]]
    retrieved_memory: List[Dict[str, Any]]
    kg_context: Dict[str, Any]
    personality_state: Dict[str, float]

    # 输出
    response: str

    # 元数据
    timestamp: str
    analysis: Dict[str, Any]


class VirtualIdolAgent:
    """虚拟偶像代理"""

    def __init__(self, session_id: Optional[str] = None):
        """
        初始化代理

        Args:
            session_id: 会话 ID
        """
        self.session_id = session_id or settings.SESSION_ID
        self.llm_manager = get_llm_manager()
        self.vector_store = get_vector_store()
        self.kg_manager = get_kg_manager()
        self.personality_model = create_personality_model()
        self.personality_evolver = create_personality_evolver()

        # 构建图
        self.graph = self._build_graph()
        self.chat_history: List[Dict[str, str]] = []

        print(f"✅ 虚拟偶像代理初始化成功 (会话: {self.session_id})")

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph"""
        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("retrieve_memory", self._retrieve_memory_node)
        workflow.add_node("query_knowledge_graph", self._query_kg_node)
        workflow.add_node("evolve_personality", self._evolve_personality_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("update_knowledge", self._update_kg_node)

        # 设置入口点
        workflow.set_entry_point("retrieve_memory")

        # 添加边
        workflow.add_edge("retrieve_memory", "query_knowledge_graph")
        workflow.add_edge("query_knowledge_graph", "evolve_personality")
        workflow.add_edge("evolve_personality", "generate_response")
        workflow.add_edge("generate_response", "update_knowledge")
        workflow.add_edge("update_knowledge", END)

        # 编译图
        return workflow.compile()

    def _retrieve_memory_node(self, state: AgentState) -> AgentState:
        """检索历史记忆（向量搜索）"""
        print(f"\n🔍 节点 1: 检索历史记忆")

        query = state["message"]

        try:
            # 从向量数据库检索相关历史
            results = self.vector_store.search(
                query=query,
                session_id=self.session_id,
                k=settings.K_RETRIEVAL
            )

            # 转换为可读格式
            retrieved = []
            for doc in results:
                retrieved.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })

            state["retrieved_memory"] = retrieved
            print(f"  ✅ 检索到 {len(retrieved)} 条相关记忆")

        except Exception as e:
            print(f"  ⚠️  记忆检索失败: {e}")
            state["retrieved_memory"] = []

        return state

    def _query_kg_node(self, state: AgentState) -> AgentState:
        """查询知识图谱"""
        print(f"\n🕸️  节点 2: 查询知识图谱")

        query = state["message"]

        try:
            # 从知识图谱查询相关子图
            results = self.kg_manager.query_relevant_subgraph(
                query_text=query,
                session_id=self.session_id,
                limit=10
            )

            # 获取用户偏好
            preferences = self.kg_manager.get_user_preferences(
                session_id=self.session_id,
                limit=5
            )

            state["kg_context"] = {
                "subgraph": results[:5],  # 限制数量
                "preferences": preferences
            }

            print(f"  ✅ 查询到 {len(results)} 个图节点, {len(preferences)} 个偏好")

        except Exception as e:
            print(f"  ⚠️  知识图谱查询失败: {e}")
            state["kg_context"] = {"subgraph": [], "preferences": []}

        return state

    def _evolve_personality_node(self, state: AgentState) -> AgentState:
        """进化性格"""
        print(f"\n🎭 节点 3: 进化性格")

        user_input = state["message"]

        try:
            # 分析用户输入对性格的影响
            new_state = self.personality_evolver.evolve(user_input)
            state["personality_state"] = new_state.to_dict()

            print(f"  ✅ 性格已更新")
            print(f"     主导特质: {new_state.get_dominant_traits()[0][0]}")

        except Exception as e:
            print(f"  ⚠️  性格进化失败: {e}")
            state["personality_state"] = self.personality_model.get_current_state().to_dict()

        return state

    def _generate_response_node(self, state: AgentState) -> AgentState:
        """生成响应"""
        print(f"\n💬 节点 4: 生成响应")

        # 意图识别
        intent_recognizer = get_intent_recognizer()
        intent = intent_recognizer.recognize(state["message"])
        intent_guidance = intent_recognizer.generate_response_guidance(intent)

        print(f"  🎯 意图识别: {intent['intent_type']}")
        if intent.get("should_be_proactive"):
            print(f"  ✨ 应主动对话！")

        # 构建系统提示词
        personality_dict = state["personality_state"]

        # 构建上下文
        retrieved_context = self._format_retrieved_memory(state["retrieved_memory"])
        user_preferences = self._format_preferences(state["kg_context"]["preferences"])
        recent_topics = self._extract_topics(state["retrieved_memory"])

        system_prompt = get_system_prompt(
            name=IDOL_PERSONA["name"],
            age=IDOL_PERSONA["age"],
            personality=personality_dict,
            background=IDOL_PERSONA["background"],
            speaking_style=IDOL_PERSONA["speaking_style"],
            retrieved_context=retrieved_context,
            user_preferences=user_preferences,
            recent_topics=recent_topics
        )

        # 添加意图指导到 prompt
        enhanced_prompt = f"{state['message']}\n\n{intent_guidance}"

        try:
            # 使用历史对话生成响应
            response = self.llm_manager.generate_with_history(
                prompt=enhanced_prompt,
                chat_history=self.chat_history,
                system_prompt=system_prompt
            )

            state["response"] = response
            print(f"  ✅ 响应生成成功")

        except Exception as e:
            print(f"  ⚠️  响应生成失败: {e}")
            state["response"] = f"抱歉，我现在有点困惑... 能再说一遍吗？"

        return state

    def _update_kg_node(self, state: AgentState) -> AgentState:
        """更新知识图谱"""
        print(f"\n📊 节点 5: 更新知识图谱")

        # 构建对话文本
        dialogue = f"用户: {state['message']}\n偶像: {state['response']}"

        try:
            # 抽取实体和关系并存储
            stats = self.kg_manager.extract_and_store(
                dialogue=dialogue,
                session_id=self.session_id
            )

            state["analysis"] = {
                "kg_updated": True,
                "stats": stats
            }

            print(f"  ✅ 知识图谱已更新")

        except Exception as e:
            print(f"  ⚠️  知识图谱更新失败: {e}")
            state["analysis"] = {"kg_updated": False, "error": str(e)}

        return state

    def _format_retrieved_memory(self, retrieved: List[Dict[str, Any]]) -> str:
        """格式化检索到的记忆"""
        if not retrieved:
            return "暂无相关历史"

        formatted = []
        for i, item in enumerate(retrieved[:3], 1):
            formatted.append(f"{i}. {item['content'][:100]}...")

        return "\n".join(formatted)

    def _format_preferences(self, preferences: List[Dict[str, Any]]) -> str:
        """格式化用户偏好"""
        if not preferences:
            return "暂无偏好记录"

        formatted = []
        for pref in preferences[:5]:
            pref_text = f"- {pref.get('preference', 'Unknown')}"
            if pref.get("description"):
                pref_text += f": {pref['description']}"
            formatted.append(pref_text)

        return "\n".join(formatted)

    def _extract_topics(self, retrieved: List[Dict[str, Any]]) -> str:
        """提取最近讨论的话题"""
        if not retrieved:
            return "暂无最近话题"

        # 简化的话题提取
        topics = set()
        for item in retrieved[:5]:
            content = item.get("content", "")
            # 从元数据中提取话题标签（如果有）
            if "topic" in item.get("metadata", {}):
                topics.add(item["metadata"]["topic"])

        return ", ".join(list(topics)[:3]) if topics else "日常对话"

    def chat(self, message: str) -> str:
        """
        同步对话

        Args:
            message: 用户消息

        Returns:
            代理响应
        """
        # 初始化状态
        initial_state: AgentState = {
            "message": message,
            "session_id": self.session_id,
            "chat_history": self.chat_history.copy(),
            "retrieved_memory": [],
            "kg_context": {},
            "personality_state": self.personality_model.get_current_state().to_dict(),
            "response": "",
            "timestamp": datetime.now().isoformat(),
            "analysis": {}
        }

        # 执行图
        print(f"\n{'='*60}")
        print(f"🎤 用户: {message}")
        print(f"{'='*60}")

        final_state = self.graph.invoke(initial_state)

        # 更新对话历史
        self.chat_history.append({"role": "user", "content": message})
        self.chat_history.append({"role": "assistant", "content": final_state["response"]})

        # 保存到向量数据库
        try:
            self.vector_store.add_conversation(
                session_id=self.session_id,
                user_message=message,
                assistant_message=final_state["response"]
            )
        except Exception as e:
            print(f"⚠️  保存到向量数据库失败: {e}")

        print(f"\n{'='*60}")
        print(f"✨ 偶像: {final_state['response']}")
        print(f"{'='*60}\n")

        return final_state["response"]

    def stream_chat(self, message: str):
        """
        流式对话

        Args:
            message: 用户消息

        Yields:
            响应文本片段
        """
        # 先执行完整的图流程（流式只在生成阶段）
        initial_state: AgentState = {
            "message": message,
            "session_id": self.session_id,
            "chat_history": self.chat_history.copy(),
            "retrieved_memory": [],
            "kg_context": {},
            "personality_state": self.personality_model.get_current_state().to_dict(),
            "response": "",
            "timestamp": datetime.now().isoformat(),
            "analysis": {}
        }

        # 执行检索和性格更新（非流式部分）
        state = initial_state
        state = self._retrieve_memory_node(state)
        state = self._query_kg_node(state)
        state = self._evolve_personality_node(state)

        # 构建系统提示词
        personality_dict = state["personality_state"]
        system_prompt = get_system_prompt(
            name=IDOL_PERSONA["name"],
            age=IDOL_PERSONA["age"],
            personality=personality_dict,
            background=IDOL_PERSONA["background"],
            speaking_style=IDOL_PERSONA["speaking_style"],
            retrieved_context=self._format_retrieved_memory(state["retrieved_memory"]),
            user_preferences=self._format_preferences(state["kg_context"]["preferences"]),
            recent_topics=self._extract_topics(state["retrieved_memory"])
        )

        # 流式生成响应
        full_response = ""
        for chunk in self.llm_manager.stream_with_history(
            prompt=message,
            chat_history=self.chat_history,
            system_prompt=system_prompt
        ):
            full_response += chunk
            yield chunk

        # 更新知识图谱（异步，不阻塞）
        state["response"] = full_response
        self._update_kg_node(state)

        # 更新历史
        self.chat_history.append({"role": "user", "content": message})
        self.chat_history.append({"role": "assistant", "content": full_response})

        # 保存到向量数据库
        try:
            self.vector_store.add_conversation(
                session_id=self.session_id,
                user_message=message,
                assistant_message=full_response
            )
        except Exception as e:
            print(f"⚠️  保存到向量数据库失败: {e}")

    def get_personality(self) -> Dict[str, float]:
        """获取当前性格状态"""
        return self.personality_model.get_current_state().to_dict()

    def get_kg_data(self) -> Dict[str, Any]:
        """获取知识图谱数据（用于可视化）"""
        return self.kg_manager.get_graph_data(session_id=self.session_id)

    def reset_conversation(self) -> None:
        """重置对话"""
        self.chat_history = []
        print(f"✅ 对话已重置")


# 全局代理实例缓存
_agents: Dict[str, VirtualIdolAgent] = {}


def get_agent(session_id: Optional[str] = None) -> VirtualIdolAgent:
    """获取或创建代理实例"""
    session_id = session_id or settings.SESSION_ID

    if session_id not in _agents:
        _agents[session_id] = VirtualIdolAgent(session_id)

    return _agents[session_id]


if __name__ == "__main__":
    # 测试代理
    print("=== 虚拟偶像代理测试 ===\n")

    try:
        # 创建代理
        agent = VirtualIdolAgent(session_id="test_session")

        # 测试对话
        print("\n测试对话流程...\n")

        # 对话 1
        response1 = agent.chat("你好！我是新来的粉丝~")
        print(f"响应 1: {response1}\n")

        # 对话 2
        response2 = agent.chat("我喜欢听重金属音乐")
        print(f"响应 2: {response2}\n")

        # 对话 3
        response3 = agent.chat("你还记得我喜欢什么音乐吗？")
        print(f"响应 3: {response3}\n")

        # 获取性格状态
        print("当前性格状态:")
        personality = agent.get_personality()
        print(f"  开朗度: {personality['cheerfulness']:.2f}")
        print(f"  温柔度: {personality['gentleness']:.2f}")
        print(f"  元气值: {personality['energy']:.2f}")

        # 获取知识图谱数据
        print("\n知识图谱数据:")
        kg_data = agent.get_kg_data()
        print(f"  节点数: {len(kg_data['nodes'])}")
        print(f"  边数: {len(kg_data['edges'])}")

        print("\n✅ 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
