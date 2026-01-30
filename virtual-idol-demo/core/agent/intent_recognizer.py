"""
意图识别模块
识别用户对话意图，让偶像能主动开启话题
"""

from typing import Dict, Any, Optional
import re


class IntentRecognizer:
    """意图识别器"""

    def __init__(self):
        """初始化意图识别器"""
        # 好奇类关键词
        self.curiosity_keywords = [
            "你是", "你的", "你叫", "你喜欢", "你爱", "你会",
            "多大", "几岁", "哪里人", "兴趣", "爱好",
            "介绍一下", "告诉我", "说说", "关于你"
        ]

        # 分享类关键词
        self.sharing_keywords = [
            "我也", "我也是", "我也是这样", "我也有",
            "我也是这么想", "我也有同感"
        ]

        # 提问类关键词
        self.question_keywords = [
            "吗", "呢", "？", "?", "什么", "怎么", "如何", "为什么"
        ]

    def recognize(self, user_input: str) -> Dict[str, Any]:
        """
        识别用户意图

        Args:
            user_input: 用户输入

        Returns:
            意图分析结果
        """
        user_input_lower = user_input.lower()

        # 检测是否是对偶像好奇
        is_curiosity = any(kw in user_input for kw in self.curiosity_keywords)

        # 检测是否在分享
        is_sharing = any(kw in user_input for kw in self.sharing_keywords)

        # 检测是否是提问
        is_question = any(kw in user_input for kw in self.question_keywords)

        # 检测情感倾向
        positive_emotion = self._detect_positive_emotion(user_input)
        negative_emotion = self._detect_negative_emotion(user_input)

        # 判断意图类型
        intent_type = "normal"
        if is_curiosity:
            intent_type = "curiosity"
        elif is_sharing:
            intent_type = "sharing"
        elif negative_emotion:
            intent_type = "seeking_comfort"

        return {
            "intent_type": intent_type,
            "is_curiosity": is_curiosity,
            "is_sharing": is_sharing,
            "is_question": is_question,
            "positive_emotion": positive_emotion,
            "negative_emotion": negative_emotion,
            "should_be proactive": is_curiosity or is_sharing
        }

    def _detect_positive_emotion(self, text: str) -> bool:
        """检测积极情感"""
        positive_keywords = [
            "开心", "高兴", "喜欢", "爱", "棒", "好", "谢谢",
            "哈哈", "嘿嘿", "嘻嘻", "😊", "😄", "🎉", "太棒了"
        ]
        return any(kw in text for kw in positive_keywords)

    def _detect_negative_emotion(self, text: str) -> bool:
        """检测消极情感"""
        negative_keywords = [
            "难过", "伤心", "不喜欢", "讨厌", "不好", "累", "烦",
            "😢", "😞", "💔", "压力大", "不开心"
        ]
        return any(kw in text for kw in negative_keywords)

    def generate_response_guidance(self, intent: Dict[str, Any]) -> str:
        """
        根据意图生成响应指导

        Args:
            intent: 意图分析结果

        Returns:
            响应指导文本
        """
        if intent["intent_type"] == "curiosity":
            return """
【提示：用户对你很好奇！】
- 可以主动分享更多关于自己的事情
- 介绍自己的兴趣、经历、梦想
- 分享一些小故事或趣事
- 不要只回答，可以主动延展话题
"""
        elif intent["intent_type"] == "sharing":
            return """
【提示：用户在分享感受！】
- 表达理解和共鸣
- 分享自己的相似经历
- 加深情感连接
"""
        elif intent["intent_type"] == "seeking_comfort":
            return """
【提示：用户需要安慰！】
- 表现出同理心
- 温柔地安慰和鼓励
- 不要急着给建议，先倾听
"""
        elif intent["is_question"]:
            return """
【提示：用户在提问！】
- 直接回答问题
- 可以适当反问，但不要每次都问
- 保持自然对话节奏
"""
        else:
            return """
【提示：正常对话】
- 自然回应
- 可以主动引入话题
- 不要每次都问问题
"""


# 全局实例
_intent_recognizer: Optional[IntentRecognizer] = None


def get_intent_recognizer() -> IntentRecognizer:
    """获取全局意图识别器实例"""
    global _intent_recognizer
    if _intent_recognizer is None:
        _intent_recognizer = IntentRecognizer()
    return _intent_recognizer


if __name__ == "__main__":
    # 测试意图识别
    recognizer = IntentRecognizer()

    test_inputs = [
        "你是哪里人？",
        "介绍一下你自己",
        "我也很喜欢音乐！",
        "今天心情不太好...",
        "你喜欢什么？"
    ]

    for input_text in test_inputs:
        print(f"\n输入: {input_text}")
        intent = recognizer.recognize(input_text)
        guidance = recognizer.generate_response_guidance(intent)
        print(f"意图类型: {intent['intent_type']}")
        print(f"是否好奇: {intent['is_curiosity']}")
        print(f"应主动: {intent['should_be proactive']}")
        print(f"指导:\n{guidance}")
