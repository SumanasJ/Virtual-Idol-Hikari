import { GoogleGenAI } from '@google/genai';
import { getAllMemoryFacts, getLongTermMemories } from './memoryManager';
import { MemoryFact } from '../types';
import { addMemoryFact } from './memoryManager';

const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY || '' });

// 生成开场白或主动话题
export const generateOpeningTopic = async (
  longTermMemories: MemoryFact[],
  currentPersonality?: any
): Promise<{ topic: string; suggestAsMessage: boolean }> => {
  const memoryStr = longTermMemories
    .slice(-10) // 最近10条长期记忆
    .map(m => `• ${m.fact}`)
    .join('\n');

  const personalityStr = currentPersonality
    ? `\n当前性格：开朗${currentPersonality.cheerfulness?.toFixed(1)} 元气${currentPersonality.energy?.toFixed(1)}`
    : '';

  const prompt = `你是星野光，一个17岁的元气大阪虚拟偶像。
你要主动开启一个新话题，或者问候并关心用户。

【已知信息】
${memoryStr || '还没有太多回忆'}
${personalityStr}

【对话原则】
1. **保持角色真实性**：自称"光"，称呼对方为"粉丝君/酱"
2. **主动关心（重要！）**：优先表达对用户的关心，比如"最近怎么样"、"有没有好好吃饭"、"想你了"等
3. **自然互动（重要！）**：使用口语化表达，更自然地分享想法、经历或评论。提问概率约50%。
4. **简洁自然**：回复尽量简洁自然，1-2句话即可
5. **主动分享（重要！）**：可以主动分享自己的近况、心情、喜欢的事物等，不只是问候

返回JSON格式：
{
  "topic": "要说的内容（1-2句大阪腔口语，优先关心用户或主动分享）",
  "suggestAsMessage": true
}`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: { responseMimeType: 'application/json' }
    });

    const result = JSON.parse(response.text || '{"topic": "呀吼！今天也是元气满满的一天呢~★", "suggestAsMessage": true}');
    return result;
  } catch (error) {
    console.error('生成话题失败:', error);
    return {
      topic: '呀吼！今天也是元气满满的一天呢~有什么想聊的吗？★',
      suggestAsMessage: true
    };
  }
};

// 总结长期记忆并保存为新的长期记忆
export const summarizeLongTermMemories = async (
  longTermMemories: MemoryFact[]
): Promise<{ summarized: number; summaries: string[] }> => {
  if (longTermMemories.length < 8) return { summarized: 0, summaries: [] }; // 记忆太少不需要总结

  const prompt = `你是星野光的记忆整理助手。以下是${longTermMemories.length}条长期记忆：

${longTermMemories.map((m, i) => `${i + 1}. ${m.fact}`).join('\n')}

请将这些记忆总结成3-5条**核心回忆**：
1. 每条10-15字
2. 保留最重要的信息
3. 合并重复或相似的记忆
4. 删除琐碎的细节

返回JSON格式：
{
  "summaries": [
    "核心记忆1",
    "核心记忆2",
    ...
  ]
}`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: { responseMimeType: 'application/json' }
    });

    const result = JSON.parse(response.text || '{"summaries": []}');
    const summaries = result.summaries || [];

    // 保存总结后的记忆为新的长期记忆
    for (const summary of summaries) {
      await addMemoryFact({
        fact: summary,
        category: 'shared_event',
        type: 'long_term',
        importance: 0.8,
        source: 'system'
      });
    }

    console.log(`📝 总结了 ${summaries.length} 条核心记忆`);
    return { summarized: summaries.length, summaries };
  } catch (error) {
    console.error('总结记忆失败:', error);
    return { summarized: 0, summaries: [] };
  }
};
