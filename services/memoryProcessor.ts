import { GoogleGenAI } from '@google/genai';
import { addMemoryFact, addRelation, getShortTermMemories, promoteToLongTerm, batchPromoteToLongTerm, getLongTermMemories, deleteMemoryFact } from './memoryManager';
import { MemoryFact } from '../types';
import { summarizeLongTermMemories } from './topicGenerator';

const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY || '' });

// 简单的去重检查（检查是否已有相似的记忆）
const isDuplicateMemory = async (fact: string): Promise<boolean> => {
  const shortTermMemories = await getShortTermMemories();
  const longTermMemories = await getLongTermMemories();
  const allMemories = [...shortTermMemories, ...longTermMemories];

  // 检查是否有完全相同或高度相似的记忆
  return allMemories.some(m => {
    // 完全相同
    if (m.fact === fact) return true;
    // 包含关系（fact包含已存在的，或已存在的包含fact）
    if (m.fact.includes(fact) || fact.includes(m.fact)) {
      // 只有当长度差异不大时才认为是重复
      const lengthDiff = Math.abs(m.fact.length - fact.length);
      return lengthDiff <= 3;
    }
    return false;
  });
};

// 记录对话到短期记忆
export const recordConversationMemory = async (
  userMessage: string,
  assistantMessage: string,
  simulatedTime: string
): Promise<void> => {
  const prompt = `你是一个轻量级的记录助手。从对话中识别**真正重要**的信息。

对话：
用户：${userMessage}
光：${assistantMessage}

【记录标准】只记录以下类型：
1. **长期偏好**：明确的喜好、厌恶、习惯（如"讨厌香菜"、"喜欢早上跑步"）
2. **重要事实**：用户的基本信息、重要事件
3. **光的重要事项**：光自己的重要决定、目标

【不要记录】
- 闲聊、日常琐事
- 暂时想法、短期计划
- 吃什么、穿什么等小事
- 已经说过的重复内容
- 问候语、客套话

【要求】
- 每次最多1条
- 10-15字
- 宁可不记录，也不要记录琐事

返回JSON格式：
{
  "fact": "重要的偏好或事实（10-15字）",
  "category": "userinfo|hikari_info",
  "importance": 0.1-1.0
}

如果没有重要信息，返回 null`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: { responseMimeType: 'application/json' }
    });

    const result = JSON.parse(response.text || '{}');

    // 只记录重要事实，且去重
    if (result.fact) {
      // 检查是否重复
      const isDuplicate = await isDuplicateMemory(result.fact);
      if (isDuplicate) {
        console.log('⚠️ 记忆已存在，跳过记录');
        return;
      }

      await addMemoryFact({
        fact: result.fact,
        category: result.category || 'shared_event',
        type: 'short_term',
        importance: result.importance || 0.6,
        source: 'conversation'
      });
      console.log('📝 记录了 1 条重要信息');
    }
  } catch (error) {
    console.error('记录记忆失败:', error);
  }
};

// 整理短期记忆到长期记忆
export const organizeMemories = async (): Promise<{ promoted: number, removed: number }> => {
  const shortTermMemories = await getShortTermMemories();

  if (shortTermMemories.length < 5) {
    return { promoted: 0, removed: 0 };
  }

  const prompt = `你是星野光，以下是最近的短期记忆（${shortTermMemories.length}条）：
${shortTermMemories.map((m, i) => `${i + 1}. ${m.fact} (重要性: ${m.importance || 0.5})`).join('\n')}

请选择哪些记忆应该提升为长期记忆：
- 选择标准：重要、有意义、值得长久保存的回忆
- 返回要保留的短期记忆编号列表（如 [1, 3, 5]）
- 其余的短期记忆将被删除
- 最多保留 40% 的短期记忆

返回JSON格式：
{
  "keep_indices": [编号列表],
  "reason": "选择理由简述"
}`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: { responseMimeType: 'application/json' }
    });

    const result = JSON.parse(response.text || '{"keep_indices": [], "reason": ""}');
    const keepIndices = new Set(result.keep_indices || []);

    // 提升重要的短期记忆到长期记忆
    let promoted = 0;
    for (let i = 0; i < shortTermMemories.length; i++) {
      if (keepIndices.has(i + 1)) {
        await promoteToLongTerm(shortTermMemories[i].id);
        promoted++;
      }
    }

    // 删除未被选中的短期记忆
    // 注意：这里需要在 memoryManager 中实现删除功能
    const removed = shortTermMemories.length - promoted;

    return { promoted, removed };
  } catch (error) {
    console.error('整理记忆失败:', error);
    // 失败时保留前40%
    const keepCount = Math.floor(shortTermMemories.length * 0.4);
    for (let i = 0; i < keepCount; i++) {
      await promoteToLongTerm(shortTermMemories[i].id);
    }
    return { promoted: keepCount, removed: shortTermMemories.length - keepCount };
  }
};

// 整理并总结长期记忆（每天调用一次）
export const organizeAndSummarizeLongTerm = async (): Promise<{ promoted: number; summarized: number }> => {
  const longTermMemories = await getLongTermMemories();

  // 先处理短期记忆
  const { promoted, removed } = await organizeMemories();

  // 如果长期记忆超过8条，进行总结
  let summarized = 0;
  if (longTermMemories.length >= 8) {
    const result = await summarizeLongTermMemories(longTermMemories);
    summarized = result.summarized;

    // 删除原始的长期记忆（已经被总结替代）
    if (summarized > 0) {
      for (const mem of longTermMemories) {
        await deleteMemoryFact(mem.id);
      }
    }
  }

  return { promoted, summarized };
};

// 检查是否需要记录记忆（每1-3轮更新短期记忆）
export const shouldRecordMemory = (conversationRounds: number): boolean => {
  // 每2轮记录一次，或50%概率随机记录
  // 确保每1-3轮就有一次记录机会，且有去重逻辑避免重复
  return conversationRounds % 2 === 0 || Math.random() > 0.5;
};

// 检查是否需要整理记忆
export const shouldOrganizeMemories = async (shortTermThreshold = 15): Promise<boolean> => {
  const shortTermMemories = await getShortTermMemories();
  return shortTermMemories.length >= shortTermThreshold;
};

// 从对话历史中批量提取重要记忆
export const extractMemoriesFromHistory = async (
  messages: Array<{ role: string; content: string; timestamp: string }>,
  simulatedTime: string
): Promise<{ count: number; memories: MemoryFact[] }> => {
  if (messages.length === 0) return 0;

  // 将消息配对（用户+助手）
  // 更灵活的配对逻辑：找到用户消息，然后找下一个有文本的助手消息
  const conversationPairs: Array<{ user: string; assistant: string }> = [];
  let i = 0;
  while (i < messages.length) {
    const msg = messages[i];
    if (msg.role === 'user' && msg.content) {
      // 找到下一个有文本内容的助手消息
      for (let j = i + 1; j < messages.length; j++) {
        const nextMsg = messages[j];
        if (nextMsg.role === 'assistant' && nextMsg.content && !nextMsg.imageUrl) {
          conversationPairs.push({
            user: msg.content,
            assistant: nextMsg.content
          });
          i = j + 1; // 跳过已配对的消息
          break;
        }
      }
    }
    i++;
  }

  if (conversationPairs.length === 0) {
    console.log('没有找到有效的对话配对');
    return 0;
  }

  console.log(`找到 ${conversationPairs.length} 组对话配对`);

  const prompt = `你是星野光的记忆整理助手。以下是${conversationPairs.length}组对话：

${conversationPairs.map((pair, i) => `对话${i + 1}：
用户：${pair.user}
光：${pair.assistant}
`).join('\n')}

请从这些对话中提取**真正重要**的信息作为长期记忆：

【记录标准】只记录以下类型：
1. **长期偏好**：明确的喜好、厌恶、习惯（如"讨厌香菜"、"喜欢早上跑步"）
2. **重要事实**：用户的基本信息、重要事件
3. **光的重要事项**：光自己的重要决定、目标

【不要记录】
- 闲聊、日常琐事
- 暂时想法、短期计划
- 吃什么、穿什么等小事
- 已经说过的重复内容
- 问候语、客套话

【要求】
- 最多提取5条最重要的
- 每条10-15字
- 宁可不记录，也不要记录琐事

返回JSON格式：
{
  "memories": [
    { "fact": "重要偏好或事实", "category": "userinfo|hikari_info", "importance": 0.1-1.0 }
  ]
}`;

  try {
    console.log('🔍 开始从对话历史提取记忆...');
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: { responseMimeType: 'application/json' }
    });

    console.log('AI 响应:', response.text);

    const result = JSON.parse(response.text || '{"memories": []}');
    const memories = result.memories || [];

    console.log(`解析得到 ${memories.length} 条记忆:`, memories);

    // 添加为长期记忆
    let addedCount = 0;
    const addedMemories: MemoryFact[] = [];
    for (const mem of memories) {
      if (mem.fact) {
        const newMemory = await addMemoryFact({
          fact: mem.fact,
          category: mem.category || 'shared_event',
          type: 'long_term',
          importance: mem.importance || 0.7,
          source: 'system'
        });
        addedCount++;
        addedMemories.push(newMemory);
        console.log(`✅ 添加记忆: "${newMemory.fact}"`);
      }
    }

    console.log(`📝 从对话历史中提取了 ${addedCount} 条重要记忆`);
    return { count: addedCount, memories: addedMemories };
  } catch (error) {
    console.error('从历史提取记忆失败:', error);
    return { count: 0, memories: [] };
  }
};

// 测试：查看对话配对结果（调试用）
export const debugConversationPairs = (
  messages: Array<{ role: string; content: string; timestamp: string }>
): void => {
  console.log('=== 调试：消息列表 ===');
  console.log('总消息数:', messages.length);
  messages.forEach((msg, i) => {
    console.log(`${i + 1}. [${msg.role}] ${msg.imageUrl ? '(图片)' : ''} "${msg.content.substring(0, 50)}${msg.content.length > 50 ? '...' : ''}"`);
  });

  const conversationPairs: Array<{ user: string; assistant: string }> = [];
  let i = 0;
  while (i < messages.length) {
    const msg = messages[i];
    if (msg.role === 'user' && msg.content) {
      for (let j = i + 1; j < messages.length; j++) {
        const nextMsg = messages[j];
        if (nextMsg.role === 'assistant' && nextMsg.content && !nextMsg.imageUrl) {
          conversationPairs.push({
            user: msg.content,
            assistant: nextMsg.content
          });
          i = j + 1;
          break;
        }
      }
    }
    i++;
  }

  console.log('=== 配对结果 ===');
  console.log(`找到 ${conversationPairs.length} 组对话配对`);
  conversationPairs.forEach((pair, i) => {
    console.log(`配对 ${i + 1}:`);
    console.log(`  用户: "${pair.user}"`);
    console.log(`  光: "${pair.assistant}"`);
  });
};
