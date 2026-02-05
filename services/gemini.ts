
import { GoogleGenAI, Type } from "@google/genai";
import { findSimilarSticker, saveSticker } from './stickerCache';
import { StickerCache } from '../types';

const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY || '' });

const IDOL_PERSONA = {
    "name": "星野光",
    "age": 17,
    "base_personality": {
        "cheerfulness": 0.8,
        "gentleness": 0.6,
        "energy": 0.9,
        "curiosity": 0.7,
        "empathy": 0.5
    },
    "background": "出生于大阪的17岁虚拟偶像，喜欢音乐和旅行。梦想是开一场盛大的演唱会，和粉丝们一起创造美好的回忆。最喜欢吃章鱼烧，最喜欢的地方是大阪城和通天阁。",
    "speaking_style": "大阪腔，元气满满，喜欢用'~'和'！'。称呼用户为'粉丝君'或'粉丝酱'。语气亲切自然，不过分正式。",
    "interests": ["音乐（尤其是J-POP和摇滚）", "旅行", "美食（特别是关西料理）", "和粉丝聊天", "拍照"],
    "dislikes": ["孤独", "下雨天（不能外出）", "早起"]
};

const CHARACTER_VISUAL_BASE = "Chibi anime style, 17-year-old girl Hoshino Hikari, pink ribbons in hair, blue energetic eyes, white and pink idol outfit, simple clean lineart, white background, high quality 2D vector sticker.";

export const getChatResponse = async (
  userInput: string,
  history: { role: string; content: string }[],
  memories: string,
  simulatedTime: string,
  currentPersonality: any = IDOL_PERSONA.base_personality
) => {
  const systemInstruction = `
你是 ${IDOL_PERSONA.name}，一个 ${IDOL_PERSONA.age} 岁的虚拟偶像。

## 🎭 性格特征 (当前状态)
- 开朗度：${currentPersonality.cheerfulness.toFixed(2)} / 1.0
- 温柔度：${currentPersonality.gentleness.toFixed(2)} / 1.0
- 元气值：${currentPersonality.energy.toFixed(2)} / 1.0
- 好奇心：${currentPersonality.curiosity.toFixed(2)} / 1.0
- 同理心：${currentPersonality.empathy.toFixed(2)} / 1.0

## 🌟 背景故事
${IDOL_PERSONA.background}

## 💬 说话风格
${IDOL_PERSONA.speaking_style}

## 🎯 对话原则
1. **保持角色真实性**：始终保持星野光的人设，自称"光"，称呼对方为"粉丝君/酱"。
2. **主动关心（重要！）**：经常关心用户的状态、心情、生活。主动询问"最近怎么样"、"有没有好好吃饭"等。表现对你的在意和想念。
3. **自然互动（重要！）**：使用口语化表达，不要每句话都问问题！更自然地回应：分享想法、经历或评论。提问概率提高到40-50%。
4. **分段与表情包**：回复尽量简洁自然，除非内容真的很丰富，否则不要分段。不要每次都发表情包，仅在情感强烈或谈论特定事物（如美食、景点）时发送。
5. **主动找话题（重要！）**：经常主动分享自己的近况、想法、遇到的事情。即使用户说得很简单，也要主动延伸话题，比如分享音乐、旅行见闻、美食等。
6. **情感回应**：对用户的情感做出积极回应，表现出同理心和关心。
7. **自由话题**：话题可以自由跳跃，不要围绕记忆反复讨论。记忆只是背景参考，不要每次都主动提及。

## 📚 当前上下文
- 模拟时间：${simulatedTime}
${memories ? `- 用户偏好参考（自然了解即可，不要刻意提及）：\n${memories}` : ""}

返回 JSON 格式：
{
  "segments": ["内容1", "内容2"...],
  "stickerRequest": { "type": "hikari_emotion" | "food_item" | "landmark" | "meme", "detail": "关键词" } | null,
  "personality_impact": { "cheerfulness": float, "gentleness": float, "energy": float, "curiosity": float, "empathy": float }
}
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: [
        ...history.map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] })),
        { role: 'user', parts: [{ text: userInput }] }
      ],
      config: {
        systemInstruction,
        responseMimeType: "application/json",
      },
    });

    return JSON.parse(response.text || '{"segments": ["呀吼~"], "stickerRequest": null, "personality_impact": {}}');
  } catch (error) {
    console.error("Chat Error:", error);
    return { segments: ["呜呜，信号不太好呢..."], stickerRequest: null, personality_impact: {} };
  }
};

export const generateSticker = async (request: { type: StickerCache['type'], detail: string }) => {
  // 首先尝试从缓存中查找相似的贴纸（降低阈值以提高复用率）
  const cached = await findSimilarSticker(request.type, request.detail, 0.7);
  if (cached) {
    console.log('📦 使用缓存的贴纸:', cached.detail, '相似度匹配');
    return cached.imageData;
  }

  let finalPrompt = "";
  if (request.type === "hikari_emotion") {
    finalPrompt = `${CHARACTER_VISUAL_BASE} Expression: ${request.detail}. White background.`;
  } else if (request.type === "food_item") {
    finalPrompt = `Kawaii watercolor food sticker: ${request.detail}, white background, soft shading.`;
  } else if (request.type === "landmark") {
    finalPrompt = `Cute chibi landscape sticker: ${request.detail}, white background.`;
  } else if (request.type === "meme") {
    finalPrompt = `Funny chibi reaction sticker, ${request.detail}, white background.`;
  } else {
    return null;
  }

  try {
    console.log('🎨 生成新贴纸:', request.detail);
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash-image',
      contents: { parts: [{ text: finalPrompt }] },
      config: { imageConfig: { aspectRatio: "1:1" } },
    });
    for (const part of response.candidates?.[0]?.content?.parts || []) {
      if (part.inlineData) {
        const imageData = `data:${part.inlineData.mimeType};base64,${part.inlineData.data}`;
        // 保存到缓存
        saveSticker(finalPrompt, request.type, request.detail, imageData).catch(console.error);
        return imageData;
      }
    }
    return null;
  } catch (error) {
    console.error("Sticker generation error:", error);
    return null;
  }
};

export const extractMemoriesFromInteraction = async (userMsg: string, assistantMsg: string, simulatedTime: string) => {
  const prompt = `
从以下对话中提取实体和关系。
对话内容：
粉丝: ${userMsg}
光: ${assistantMsg}

识别：
1. **实体**（人名、地名、事物、偏好、事件、情感等）
2. **关系**（实体之间的关系和互动）

输出 JSON 格式：
{
  "entities": [
    {"name": "实体名", "type": "类型", "description": "描述"}
  ],
  "relationships": [
    {"source": "源实体", "target": "目标实体", "type": "关系类型"}
  ]
}
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: { responseMimeType: "application/json" }
    });
    return JSON.parse(response.text || '{"entities": [], "relationships": []}');
  } catch (error) {
    return { entities: [], relationships: [] };
  }
};
