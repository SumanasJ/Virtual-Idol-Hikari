import { ChatSession, Message } from '../types';

const DB_NAME = 'HikariChatSessions';
const DB_VERSION = 1;
const STORE_NAME = 'sessions';

let db: IDBDatabase | null = null;

// 初始化 IndexedDB
export const initSessionDB = (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    if (db) return resolve(db);

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      db = request.result;
      resolve(db);
    };

    request.onupgradeneeded = (event) => {
      const database = (event.target as IDBOpenDBRequest).result;
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        const store = database.createObjectStore(STORE_NAME, { keyPath: 'id' });
        store.createIndex('createdAt', 'createdAt', { unique: false });
        store.createIndex('updatedAt', 'updatedAt', { unique: false });
      }
    };
  });
};

// 生成会话标题（基于第一条消息）
const generateTitle = (messages: Message[]): string => {
  if (messages.length === 0) return '新对话';

  const firstUserMsg = messages.find(m => m.role === 'user');
  if (firstUserMsg) {
    const content = firstUserMsg.content;
    return content.length > 20 ? content.substring(0, 20) + '...' : content;
  }

  return '新对话';
};

// 创建新会话
export const createSession = async (firstMessage?: Message): Promise<ChatSession> => {
  const database = await initSessionDB();

  const now = new Date().toISOString();
  const session: ChatSession = {
    id: `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    title: firstMessage ? generateTitle([firstMessage]) : '新对话',
    messages: firstMessage ? [firstMessage] : [],
    createdAt: now,
    updatedAt: now,
    lastVisitTime: now, // 添加最后访问时间
    personality: {
      cheerfulness: 0.8,
      gentleness: 0.6,
      energy: 0.9,
      curiosity: 0.7,
      empathy: 0.5
    }
  };

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.add(session);

    request.onsuccess = () => resolve(session);
    request.onerror = () => reject(request.error);
  });
};

// 获取所有会话
export const getAllSessions = async (): Promise<ChatSession[]> => {
  const database = await initSessionDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = () => {
      const sessions = request.result as ChatSession[];
      // 按更新时间倒序排列
      resolve(sessions.sort((a, b) =>
        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      ));
    };
    request.onerror = () => reject(request.error);
  });
};

// 获取单个会话
export const getSession = async (sessionId: string): Promise<ChatSession | null> => {
  const database = await initSessionDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get(sessionId);

    request.onsuccess = () => resolve(request.result as ChatSession || null);
    request.onerror = () => reject(request.error);
  });
};

// 更新会话
export const updateSession = async (session: ChatSession): Promise<void> => {
  const database = await initSessionDB();

  // 更新标题（基于第一条用户消息）
  if (session.messages.length > 0) {
    session.title = generateTitle(session.messages);
  }

  session.updatedAt = new Date().toISOString();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.put(session);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

// 添加消息到会话
export const addMessageToSession = async (
  sessionId: string,
  message: Message,
  personality?: ChatSession['personality']
): Promise<void> => {
  const session = await getSession(sessionId);
  if (!session) throw new Error('Session not found');

  session.messages.push(message);

  if (personality) {
    session.personality = personality;
  }

  await updateSession(session);
};

// 删除会话
export const deleteSession = async (sessionId: string): Promise<void> => {
  const database = await initSessionDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.delete(sessionId);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

// 清空所有会话
export const clearAllSessions = async (): Promise<void> => {
  const database = await initSessionDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.clear();

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

// 更新会话标题
export const updateSessionTitle = async (sessionId: string, newTitle: string): Promise<void> => {
  const session = await getSession(sessionId);
  if (!session) throw new Error('Session not found');

  session.title = newTitle;
  await updateSession(session);
};
