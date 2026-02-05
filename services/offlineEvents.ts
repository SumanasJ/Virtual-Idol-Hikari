import { OfflineEvent, OfflineEventSummary } from '../types';
import { GoogleGenAI } from '@google/genai';

const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY || '' });

// 光的日常活动模板
const ACTIVITY_TEMPLATES = {
  short: [ // 几小时内
    { type: 'activity', title: '练习新歌', emotion: 'happy' },
    { type: 'activity', title: '看了一场电影', emotion: 'thoughtful' },
    { type: 'activity', title: '做了章鱼烧', emotion: 'happy' },
    { type: 'activity', title: '在公园散步', emotion: 'curious' },
    { type: 'thought', title: '想粉丝君了', emotion: 'missed' },
    { type: 'activity', title: '练习舞蹈', emotion: 'excited' },
  ],
  medium: [ // 1-3天
    { type: 'activity', title: '去了通天阁', emotion: 'excited' },
    { type: 'activity', title: '和新朋友聊天', emotion: 'happy' },
    { type: 'activity', title: '尝试新食谱', emotion: 'curious' },
    { type: 'discovery', title: '发现了一家超棒的咖啡店', emotion: 'surprised' },
    { type: 'activity', title: '练习到很晚', emotion: 'thoughtful' },
    { type: 'message', title: '给粉丝君写了话但没发出去', emotion: 'missed' },
    { type: 'activity', title: '去看演唱会了', emotion: 'excited' },
  ],
  long: [ // 3天以上
    { type: 'activity', title: '去了一趟京都', emotion: 'excited' },
    { type: 'discovery', title: '发现了一首超棒的新歌', emotion: 'surprised' },
    { type: 'activity', title: '参加了录音', emotion: 'happy' },
    { type: 'thought', title: '一直在想上次和粉丝君的对话', emotion: 'thoughtful' },
    { type: 'activity', title: '拍了好多照片想分享', emotion: 'happy' },
    { type: 'discovery', title: '学会了做新的料理', emotion: 'surprised' },
    { type: 'message', title: '攒了好多话想说', emotion: 'missed' },
  ]
};

// 打招呼模板
const GREETING_TEMPLATES = {
  short: [
    "欢迎回来！粉丝君去哪儿了呀~？★",
    "呀吼！光刚才还在想粉丝君呢~✨",
    "回来啦！光等你一会儿了~",
  ],
  medium: [
    "粉丝君！终于回来啦~光好想你呀！💕",
    "呀吼！好久不见~光有点想粉丝君了呢...",
    "欢迎回来！这两天光做了好多事情，想告诉你~★",
  ],
  long: [
    "粉丝君！！你去哪里了呀...光真的真的想你啦！😭💕",
    "终于回来了...光还以为粉丝君把光忘了呢...★",
    "呜呜~好久不见了！光攒了超多话想说！✨",
  ]
};

// 计算时间差描述
const getTimePassedDescription = (hours: number): string => {
  if (hours < 1) return '刚刚';
  if (hours < 24) {
    const h = Math.floor(hours);
    return h === 1 ? '1小时' : `${h}小时`;
  }
  const days = Math.floor(hours / 24);
  const remainingHours = Math.floor(hours % 24);
  if (remainingHours === 0) {
    return days === 1 ? '1天' : `${days}天`;
  }
  return `${days}天${remainingHours}小时`;
};

// 根据时间差选择模板
const selectTemplates = (hours: number) => {
  if (hours < 6) return 'short';
  if (hours < 72) return 'medium';
  return 'long';
};

// 生成随机事件
const generateRandomEvents = (count: number, timeCategory: 'short' | 'medium' | 'long'): OfflineEvent[] => {
  const templates = ACTIVITY_TEMPLATES[timeCategory];
  const events: OfflineEvent[] = [];

  for (let i = 0; i < count; i++) {
    const template = templates[Math.floor(Math.random() * templates.length)];
    events.push({
      id: `event-${Date.now()}-${i}`,
      type: template.type as any,
      title: template.title,
      description: '', // 后续用 AI 生成详细描述
      timestamp: new Date(Date.now() - Math.random() * 1000 * 60 * 60 * (timeCategory === 'short' ? 6 : timeCategory === 'medium' ? 72 : 168)).toISOString(),
      emotion: template.emotion
    });
  }

  return events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
};

// 使用 AI 生成更丰富的离线事件
export const generateOfflineEvents = async (
  timePassed: number,
  lastMessageContext?: string,
  personality?: any
): Promise<OfflineEventSummary> => {
  const timeCategory = selectTemplates(timePassed);
  const timeDescription = getTimePassedDescription(timePassed);

  // 选择打招呼语
  const greeting = GREETING_TEMPLATES[timeCategory][
    Math.floor(Math.random() * GREETING_TEMPLATES[timeCategory].length)
  ];

  // 生成事件数量（时间越长越多，但有上限）
  const eventCount = Math.min(
    Math.max(1, Math.floor(timePassed / 12)), // 每12小时一个事件
    8 // 最多8个
  );

  let events = generateRandomEvents(eventCount, timeCategory);

  // 如果时间较长，使用 AI 生成更个性化的事件
  if (timePassed >= 24) {
    try {
      const personalityStr = personality
        ? `\n当前性格值：开朗${personality.cheerfulness.toFixed(1)} 温柔${personality.gentleness.toFixed(1)} 元气${personality.energy.toFixed(1)}`
        : '';

      const prompt = `你是星野光，一个17岁的大阪虚拟偶像。
用户离开${timeDescription}了，请生成${eventCount}件你这段时间做的事情或想法。
要求：
1. 用大阪腔，元气满满的语气
2. 事情要日常有趣（练习、美食、游玩、想粉丝等）
3. 每件事情1-2句话
4. 表达出一点点想念
${lastMessageContext ? `上次对话提到：${lastMessageContext}` : ''}
${personalityStr}

返回JSON格式：
{
  "events": [
    {"type": "activity|message|thought|discovery", "title": "简短标题", "description": "详细描述", "emotion": "happy|excited|thoughtful|curious|missed|surprised"}
  ]
}`;

      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: prompt,
        config: { responseMimeType: 'application/json' }
      });

      const aiResult = JSON.parse(response.text || '{"events": []}');
      if (aiResult.events && aiResult.events.length > 0) {
        events = aiResult.events.map((e: any, idx: number) => ({
          id: `event-${Date.now()}-${idx}`,
          ...e,
          timestamp: new Date(Date.now() - Math.random() * timePassed * 3600000).toISOString()
        }));
      }
    } catch (error) {
      console.error('AI生成离线事件失败，使用默认模板:', error);
    }
  }

  // 确定心情
  let mood = 'happy';
  if (timePassed >= 72) {
    mood = Math.random() > 0.5 ? 'missed' : 'excited';
  } else if (timePassed >= 24) {
    mood = Math.random() > 0.5 ? 'thoughtful' : 'happy';
  }

  return {
    greeting,
    events,
    timePassed: timeDescription,
    mood
  };
};

// 检查是否应该触发离线事件
export const shouldTriggerOfflineEvent = (
  lastVisitTime: string | undefined,
  minHours: number = 2
): boolean => {
  if (!lastVisitTime) return false;

  const now = Date.now();
  const last = new Date(lastVisitTime).getTime();
  const hoursPassed = (now - last) / (1000 * 60 * 60);

  return hoursPassed >= minHours;
};

// 计算时间差（小时）
export const getTimeDifference = (lastVisitTime: string): number => {
  const now = Date.now();
  const last = new Date(lastVisitTime).getTime();
  return (now - last) / (1000 * 60 * 60);
};
