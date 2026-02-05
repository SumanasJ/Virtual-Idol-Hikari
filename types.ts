
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  imageUrl?: string;
}

export interface MemoryFact {
  id: string;
  fact: string;
  category: 'userinfo' | 'hikari_info' | 'shared_event';
  timestamp: string;
  originalEventDate?: string;
  type: 'short_term' | 'long_term'; // 短期或长期记忆
  importance?: number; // 重要性评分 0-1
  source?: 'conversation' | 'offline_event' | 'system'; // 来源
}

export interface Relation {
  id: string;
  source: string;
  predicate: string;
  target: string;
  timestamp: string;
}

export interface MemoryState {
  facts: MemoryFact[];
  relations: Relation[];
}

export interface StickerCache {
  id: string;
  prompt: string;
  type: 'hikari_emotion' | 'food_item' | 'landmark' | 'meme';
  detail: string;
  imageData: string; // base64 image data
  embedding: number[]; // text embedding vector for similarity search
  createdAt: string;
  usageCount: number;
}

export interface StickerCacheStats {
  totalCached: number;
  totalSize: number;
  hitRate: number;
  mostUsed: StickerCache[];
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  lastVisitTime?: string; // 上次访问时间
  personality: {
    cheerfulness: number;
    gentleness: number;
    energy: number;
    curiosity: number;
    empathy: number;
  };
}

export interface OfflineEvent {
  id: string;
  type: 'activity' | 'message' | 'thought' | 'discovery';
  title: string;
  description: string;
  timestamp: string;
  emotion: 'happy' | 'excited' | 'thoughtful' | 'curious' | 'missed' | 'surprised';
}

export interface OfflineEventSummary {
  greeting: string; // 打招呼语
  events: OfflineEvent[]; // 离线期间的事件
  timePassed: string; // 时间描述（如"3天2小时"）
  mood: string; // 光当前的心情
}
