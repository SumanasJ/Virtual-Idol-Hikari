"""
性格进化系统
根据用户输入分析并调整偶像性格
"""

import json
from typing import Dict, Any, Optional

from core.personality.personality_model import PersonalityModel, PersonalityState
from core.llm.llm_manager import get_llm_manager
from config.prompts import get_personality_analysis_prompt
from config.settings import settings


class PersonalityEvolver:
    """性格进化器"""

    def __init__(
        self,
        personality_model: Optional[PersonalityModel] = None
    ):
        """
        初始化性格进化器

        Args:
            personality_model: 性格模型实例
        """
        self.personality_model = personality_model or PersonalityModel()
        self.llm_manager = get_llm_manager()

    def analyze_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户输入对性格的影响

        Args:
            user_input: 用户输入文本

        Returns:
            分析结果（包含情感、话题类型、性格影响）
        """
        current_state = self.personality_model.get_current_state()
        personality_dict = current_state.to_dict()

        # 生成分析提示词
        prompt = get_personality_analysis_prompt(
            user_input=user_input,
            personality=personality_dict
        )

        try:
            # 使用 LLM 分析
            result = self.llm_manager.extract_json(prompt)

            # 验证结果格式
            if "personality_impact" not in result:
                # 如果 LLM 返回格式不对，使用规则方法
                return self._rule_based_analysis(user_input)

            return result

        except Exception as e:
            print(f"LLM 分析失败，使用规则方法: {e}")
            return self._rule_based_analysis(user_input)

    def _rule_based_analysis(self, user_input: str) -> Dict[str, Any]:
        """
        基于规则的分析（备用方法）

        Args:
            user_input: 用户输入

        Returns:
            分析结果
        """
        # 简单的关键词匹配规则
        user_input_lower = user_input.lower()

        # 情感分析
        positive_keywords = ["开心", "高兴", "喜欢", "爱", "棒", "好", "谢谢", "哈哈", "😊", "😄"]
        negative_keywords = ["难过", "伤心", "不喜欢", "讨厌", "不好", "累", "烦", "😢", "😞"]

        positive_count = sum(1 for kw in positive_keywords if kw in user_input_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in user_input_lower)

        if positive_count > negative_count:
            emotion = "positive"
        elif negative_count > positive_count:
            emotion = "negative"
        else:
            emotion = "neutral"

        # 话题类型
        topic_keywords = {
            "music": ["音乐", "歌", "歌手", "乐队", "摇滚", "流行"],
            "life": ["生活", "工作", "学习", "天气", "今天"],
            "emotion": ["心情", "感觉", "开心", "难过", "高兴"],
            "food": ["吃", "美食", "料理", "菜", "饭"],
            "travel": ["旅行", "去", "玩", "地方", "景点"]
        }

        topic_type = "other"
        max_matches = 0

        for topic, keywords in topic_keywords.items():
            matches = sum(1 for kw in keywords if kw in user_input_lower)
            if matches > max_matches:
                max_matches = matches
                topic_type = topic

        # 计算性格影响
        impact = {
            "cheerfulness": 0.0,
            "gentleness": 0.0,
            "energy": 0.0,
            "curiosity": 0.0,
            "empathy": 0.0
        }

        # 根据情感调整
        if emotion == "positive":
            impact["cheerfulness"] += 0.1
            impact["energy"] += 0.05
        elif emotion == "negative":
            impact["empathy"] += 0.15
            impact["gentleness"] += 0.1
            impact["cheerfulness"] -= 0.05

        # 根据话题调整
        if topic_type == "music":
            impact["energy"] += 0.05
            impact["curiosity"] += 0.05
        elif topic_type == "emotion":
            impact["empathy"] += 0.1
            impact["gentleness"] += 0.05
        elif topic_type == "travel":
            impact["curiosity"] += 0.1
            impact["energy"] += 0.05

        # 限制变化范围
        for trait in impact:
            impact[trait] = max(-0.2, min(0.2, impact[trait]))

        return {
            "user_emotion": emotion,
            "topic_type": topic_type,
            "personality_impact": impact
        }

    def evolve(self, user_input: str, user_feedback: Optional[str] = None) -> PersonalityState:
        """
        根据用户输入进化性格

        Args:
            user_input: 用户输入
            user_feedback: 用户反馈（可选）

        Returns:
            更新后的性格状态
        """
        # 分析用户输入
        analysis = self.analyze_user_input(user_input)

        # 获取性格影响
        impact = analysis.get("personality_impact", {})

        # 如果有用户反馈，额外考虑
        if user_feedback:
            feedback_impact = self._analyze_feedback(user_feedback)
            for trait, value in feedback_impact.items():
                impact[trait] = impact.get(trait, 0.0) + value

        # 应用性格变化
        new_state = self.personality_model.update_state(impact)

        # 打印进化信息
        print(f"📊 性格进化:")
        print(f"  用户情感: {analysis.get('user_emotion', 'unknown')}")
        print(f"  话题类型: {analysis.get('topic_type', 'unknown')}")
        print(f"  性格影响: {impact}")

        return new_state

    def _analyze_feedback(self, feedback: str) -> Dict[str, float]:
        """
        分析用户反馈

        Args:
            feedback: 用户反馈文本

        Returns:
            性格影响
        """
        feedback_lower = feedback.lower()

        impact = {}

        # 正面反馈
        if any(kw in feedback_lower for kw in ["好", "喜欢", "棒", "谢谢", "不错"]):
            impact["cheerfulness"] = 0.05
            impact["energy"] = 0.03

        # 负面反馈
        if any(kw in feedback_lower for kw in ["不好", "不喜欢", "差", "不行"]):
            impact["empathy"] = 0.1
            impact["gentleness"] = 0.05
            impact["cheerfulness"] = -0.03

        # 请求更温柔
        if any(kw in feedback_lower for kw in ["温柔", "体贴", "关心"]):
            impact["gentleness"] = 0.1
            impact["empathy"] = 0.05

        # 请求更活泼
        if any(kw in feedback_lower for kw in ["活泼", "开朗", "元气"]):
            impact["cheerfulness"] = 0.1
            impact["energy"] = 0.08

        return impact

    def should_reset(self) -> bool:
        """
        判断是否需要重置性格

        Returns:
            是否需要重置
        """
        return not self.personality_model.is_within_bounds()

    def soft_reset(self) -> None:
        """软重置：向基础值回调"""
        current_state = self.personality_model.get_current_state()
        base_personality = self.personality_model.get_base_personality()

        # 向基础值回调 50%
        delta = {}
        for trait in base_personality:
            current_value = getattr(current_state, trait)
            base_value = base_personality[trait]

            # 计算差异，回调一半
            diff = base_value - current_value
            delta[trait] = diff * 0.5

        self.personality_model.update_state(delta)
        print("⚠️  性格已软重置（向基础值回调）")

    def get_evolution_summary(self) -> Dict[str, Any]:
        """
        获取进化摘要

        Returns:
            进化摘要
        """
        current_state = self.personality_model.get_current_state()
        base_personality = self.personality_model.get_base_personality()

        summary = {
            "evolution_count": current_state.evolution_count,
            "current_state": current_state.to_dict(),
            "drift_from_base": {}
        }

        # 计算偏离度
        for trait in base_personality:
            current_value = getattr(current_state, trait)
            base_value = base_personality[trait]
            summary["drift_from_base"][trait] = current_value - base_value

        return summary


def create_personality_evolver() -> PersonalityEvolver:
    """创建性格进化器实例"""
    return PersonalityEvolver()


if __name__ == "__main__":
    # 测试性格进化器
    print("=== 性格进化器测试 ===\n")

    # 创建进化器
    evolver = create_personality_evolver()
    print("✅ 性格进化器初始化成功\n")

    # 测试分析
    print("测试 1: 分析用户输入")
    test_inputs = [
        "今天心情特别好！天气也不错~",
        "我有点难过，工作压力好大",
        "我喜欢听重金属音乐",
        "你能更温柔一点吗？"
    ]

    for input_text in test_inputs:
        print(f"\n输入: {input_text}")
        analysis = evolver.analyze_user_input(input_text)
        print(f"情感: {analysis['user_emotion']}")
        print(f"话题: {analysis['topic_type']}")
        print(f"影响: {analysis['personality_impact']}")

    print("\n" + "="*50 + "\n")

    # 测试进化
    print("测试 2: 性格进化")
    print("初始状态:")
    print(evolver.personality_model.current_state.get_description())

    # 模拟多次交互
    print("\n模拟交互...")

    evolver.evolve("今天很开心！")
    evolver.evolve("我有点难过，能安慰我吗？")
    evolver.evolve("我喜欢摇滚音乐！")
    evolver.evolve("你太棒了！")

    print("\n进化后的状态:")
    print(evolver.personality_model.current_state.get_description())

    # 测试摘要
    print("\n测试 3: 进化摘要")
    summary = evolver.get_evolution_summary()
    print(f"进化次数: {summary['evolution_count']}")
    print(f"偏离度: {summary['drift_from_base']}")

    print("\n✅ 所有测试通过！")
