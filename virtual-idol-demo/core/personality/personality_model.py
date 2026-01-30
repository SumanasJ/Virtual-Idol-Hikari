"""
性格模型
定义虚拟偶像的基础性格和状态管理
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
import json
from datetime import datetime

from config.prompts import IDOL_PERSONA
from config.settings import settings


@dataclass
class PersonalityState:
    """性格状态类"""

    # 五大性格维度
    cheerfulness: float = 0.8  # 开朗度
    gentleness: float = 0.6    # 温柔度
    energy: float = 0.9        # 元气值
    curiosity: float = 0.7     # 好奇心
    empathy: float = 0.5       # 同理心

    # 元数据
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    evolution_count: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cheerfulness": self.cheerfulness,
            "gentleness": self.gentleness,
            "energy": self.energy,
            "curiosity": self.curiosity,
            "empathy": self.empathy,
            "last_updated": self.last_updated,
            "evolution_count": self.evolution_count,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalityState':
        """从字典创建实例"""
        return cls(
            cheerfulness=data.get("cheerfulness", 0.8),
            gentleness=data.get("gentleness", 0.6),
            energy=data.get("energy", 0.9),
            curiosity=data.get("curiosity", 0.7),
            empathy=data.get("empathy", 0.5),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
            evolution_count=data.get("evolution_count", 0),
            history=data.get("history", [])
        )

    def normalize(self) -> None:
        """确保所有值在 [0, 1] 范围内"""
        self.cheerfulness = max(0.0, min(1.0, self.cheerfulness))
        self.gentleness = max(0.0, min(1.0, self.gentleness))
        self.energy = max(0.0, min(1.0, self.energy))
        self.curiosity = max(0.0, min(1.0, self.curiosity))
        self.empathy = max(0.0, min(1.0, self.empathy))

    def is_valid(self) -> bool:
        """检查状态是否有效"""
        return all(0.0 <= getattr(self, attr) <= 1.0 for attr in [
            "cheerfulness", "gentleness", "energy", "curiosity", "empathy"
        ])

    def get_dominant_traits(self, top_n: int = 3) -> List[tuple[str, float]]:
        """获取主导性格特质"""
        traits = [
            ("开朗度", self.cheerfulness),
            ("温柔度", self.gentleness),
            ("元气值", self.energy),
            ("好奇心", self.curiosity),
            ("同理心", self.empathy)
        ]
        return sorted(traits, key=lambda x: x[1], reverse=True)[:top_n]

    def get_description(self) -> str:
        """获取性格状态描述"""
        dominant = self.get_dominant_traits(2)
        desc = f"当前性格状态（已进化 {self.evolution_count} 次）：\n"

        for trait_name, value in [
            ("开朗度", self.cheerfulness),
            ("温柔度", self.gentleness),
            ("元气值", self.energy),
            ("好奇心", self.curiosity),
            ("同理心", self.empathy)
        ]:
            bar = "█" * int(value * 10)
            desc += f"  {trait_name}: {bar} {value:.2f}\n"

        desc += f"\n主导特质: {', '.join([t[0] for t in dominant])}"

        return desc


class PersonalityModel:
    """性格模型类"""

    def __init__(self, base_personality: Dict[str, float] = None):
        """
        初始化性格模型

        Args:
            base_personality: 基础性格设定
        """
        self.base_personality = base_personality or IDOL_PERSONA["base_personality"].copy()
        self.current_state = PersonalityState(**self.base_personality)

        # 性格变化限制
        self.max_drift = settings.MAX_PERSONALITY_DRIFT
        self.evolution_rate = settings.EVOLUTION_RATE

    def get_base_personality(self) -> Dict[str, float]:
        """获取基础性格"""
        return self.base_personality.copy()

    def get_current_state(self) -> PersonalityState:
        """获取当前性格状态"""
        return self.current_state

    def update_state(self, delta: Dict[str, float]) -> PersonalityState:
        """
        更新性格状态

        Args:
            delta: 各维度的变化量

        Returns:
            更新后的状态
        """
        # 记录历史
        self.current_state.history.append({
            "timestamp": datetime.now().isoformat(),
            "delta": delta.copy(),
            "previous_state": self.current_state.to_dict()
        })

        # 应用变化
        for trait, change in delta.items():
            if hasattr(self.current_state, trait):
                current_value = getattr(self.current_state, trait)
                base_value = self.base_personality.get(trait, 0.5)

                # 限制变化范围
                max_change = self.evolution_rate
                change = max(-max_change, min(max_change, change))

                # 计算新值
                new_value = current_value + change

                # 确保不偏离基础值太远
                min_allowed = max(0.0, base_value - self.max_drift)
                max_allowed = min(1.0, base_value + self.max_drift)
                new_value = max(min_allowed, min(max_allowed, new_value))

                setattr(self.current_state, trait, new_value)

        # 更新元数据
        self.current_state.last_updated = datetime.now().isoformat()
        self.current_state.evolution_count += 1

        # 确保值在有效范围内
        self.current_state.normalize()

        return self.current_state

    def reset_to_base(self) -> None:
        """重置到基础性格"""
        self.current_state = PersonalityState(**self.base_personality)

    def is_within_bounds(self) -> bool:
        """检查当前性格是否在允许范围内"""
        for trait in ["cheerfulness", "gentleness", "energy", "curiosity", "empathy"]:
            current_value = getattr(self.current_state, trait)
            base_value = self.base_personality.get(trait, 0.5)

            if abs(current_value - base_value) > self.max_drift:
                return False

        return True

    def get_personality_prompt(self) -> str:
        """获取用于 prompt 的性格描述"""
        state = self.current_state

        # 根据当前状态生成描述
        descriptions = []

        if state.cheerfulness > 0.7:
            descriptions.append("非常开朗活泼")
        elif state.cheerfulness > 0.4:
            descriptions.append("比较开朗")
        else:
            descriptions.append("比较安静")

        if state.gentleness > 0.7:
            descriptions.append("特别温柔体贴")
        elif state.gentleness > 0.4:
            descriptions.append("有点温柔")
        else:
            descriptions.append("比较直爽")

        if state.energy > 0.7:
            descriptions.append("充满活力")
        elif state.energy > 0.4:
            descriptions.append("精力充沛")
        else:
            descriptions.append("比较慵懒")

        if state.curiosity > 0.7:
            descriptions.append("对什么都很好奇")
        elif state.curiosity > 0.4:
            descriptions.append("有一定好奇心")
        else:
            descriptions.append("比较淡定")

        if state.empathy > 0.7:
            descriptions.append("非常能理解他人情感")
        elif state.empathy > 0.4:
            descriptions.append("有一定同理心")
        else:
            descriptions.append("比较关注自己")

        return "、".join(descriptions)

    def to_json(self) -> str:
        """导出为 JSON"""
        return json.dumps({
            "base_personality": self.base_personality,
            "current_state": self.current_state.to_dict()
        }, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'PersonalityModel':
        """从 JSON 导入"""
        data = json.loads(json_str)
        model = cls(base_personality=data["base_personality"])
        model.current_state = PersonalityState.from_dict(data["current_state"])
        return model


def create_personality_model() -> PersonalityModel:
    """创建性格模型实例"""
    return PersonalityModel(base_personality=IDOL_PERSONA["base_personality"].copy())


if __name__ == "__main__":
    # 测试性格模型
    print("=== 性格模型测试 ===\n")

    # 创建模型
    model = create_personality_model()
    print("✅ 性格模型初始化成功\n")

    # 显示初始状态
    print("初始性格状态:")
    print(model.current_state.get_description())
    print()

    # 测试更新
    print("测试 1: 更新性格状态")
    delta = {
        "cheerfulness": 0.1,
        "gentleness": -0.05,
        "empathy": 0.15
    }
    new_state = model.update_state(delta)
    print(f"应用变化: {delta}")
    print(new_state.get_description())
    print()

    # 测试边界检查
    print("测试 2: 边界检查")
    print(f"是否在有效范围内: {model.is_within_bounds()}")
    print()

    # 测试主导特质
    print("测试 3: 主导特质")
    dominant = model.current_state.get_dominant_traits()
    print(f"主导特质: {dominant}")
    print()

    # 测试描述生成
    print("测试 4: 生成描述")
    desc = model.get_personality_prompt()
    print(f"性格描述: {desc}")
    print()

    # 测试 JSON 导入导出
    print("测试 5: JSON 导入导出")
    json_str = model.to_json()
    print(f"导出的 JSON:\n{json_str[:200]}...")

    # 测试导入
    restored_model = PersonalityModel.from_json(json_str)
    print(f"\n恢复后的状态:")
    print(restored_model.current_state.get_description())
    print()

    print("✅ 所有测试通过！")
