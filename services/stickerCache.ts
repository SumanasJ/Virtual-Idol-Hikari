import { StickerCache, StickerCacheStats } from '../types';

const DB_NAME = 'HikariStickerCache';
const DB_VERSION = 1;
const STORE_NAME = 'stickers';

let db: IDBDatabase | null = null;

// 初始化 IndexedDB
export const initDB = (): Promise<IDBDatabase> => {
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
        store.createIndex('type', 'type', { unique: false });
        store.createIndex('detail', 'detail', { unique: false });
        store.createIndex('createdAt', 'createdAt', { unique: false });
        store.createIndex('usageCount', 'usageCount', { unique: false });
      }
    };
  });
};

// 计算简单的文本向量（TF-IDF 简化版）
const computeTextEmbedding = (text: string): number[] => {
  // 简单的字符级 n-gram 特征
  const n = 2; // 2-gram
  const features = new Map<string, number>();

  for (let i = 0; i <= text.length - n; i++) {
    const gram = text.toLowerCase().substring(i, i + n);
    features.set(gram, (features.get(gram) || 0) + 1);
  }

  // 归一化为 256 维向量（简化版）
  const vector = new Array(256).fill(0);
  let idx = 0;
  for (const [char, count] of features) {
    const hash = hashString(char);
    vector[hash % 256] += count;
    idx++;
  }

  // L2 归一化
  const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
  return magnitude > 0 ? vector.map(v => v / magnitude) : vector;
};

const hashString = (str: string): number => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash);
};

// 计算余弦相似度
export const cosineSimilarity = (vec1: number[], vec2: number[]): number => {
  if (vec1.length !== vec2.length) return 0;

  let dotProduct = 0;
  let mag1 = 0;
  let mag2 = 0;

  for (let i = 0; i < vec1.length; i++) {
    dotProduct += vec1[i] * vec2[i];
    mag1 += vec1[i] * vec1[i];
    mag2 += vec2[i] * vec2[i];
  }

  mag1 = Math.sqrt(mag1);
  mag2 = Math.sqrt(mag2);

  if (mag1 === 0 || mag2 === 0) return 0;
  return dotProduct / (mag1 * mag2);
};

// 保存贴纸到缓存
export const saveSticker = async (
  prompt: string,
  type: StickerCache['type'],
  detail: string,
  imageData: string
): Promise<StickerCache> => {
  const database = await initDB();
  const embedding = computeTextEmbedding(prompt + ' ' + detail);

  const sticker: StickerCache = {
    id: `sticker-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    prompt,
    type,
    detail,
    imageData,
    embedding,
    createdAt: new Date().toISOString(),
    usageCount: 1
  };

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.add(sticker);

    request.onsuccess = () => resolve(sticker);
    request.onerror = () => reject(request.error);
  });
};

// 搜索相似的贴纸
export const findSimilarSticker = async (
  type: StickerCache['type'],
  detail: string,
  threshold = 0.85 // 相似度阈值
): Promise<StickerCache | null> => {
  const database = await initDB();
  const queryEmbedding = computeTextEmbedding(detail);

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index('type');
    const request = index.getAll(type);

    request.onsuccess = () => {
      const stickers = request.result as StickerCache[];

      // 找到最相似的贴纸
      let bestMatch: StickerCache | null = null;
      let bestSimilarity = 0;

      for (const sticker of stickers) {
        const similarity = cosineSimilarity(queryEmbedding, sticker.embedding);
        if (similarity > bestSimilarity && similarity >= threshold) {
          bestSimilarity = similarity;
          bestMatch = sticker;
        }
      }

      if (bestMatch) {
        // 增加使用次数
        updateUsageCount(bestMatch.id).catch(console.error);
      }

      resolve(bestMatch);
    };

    request.onerror = () => reject(request.error);
  });
};

// 更新使用次数
const updateUsageCount = async (id: string): Promise<void> => {
  const database = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const getReq = store.get(id);

    getReq.onsuccess = () => {
      const sticker = getReq.result as StickerCache;
      if (sticker) {
        sticker.usageCount++;
        store.put(sticker);
      }
      resolve();
    };
    getReq.onerror = () => reject(getReq.error);
  });
};

// 获取所有缓存
export const getAllCachedStickers = async (): Promise<StickerCache[]> => {
  const database = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = () => resolve(request.result as StickerCache[]);
    request.onerror = () => reject(request.error);
  });
};

// 获取缓存统计
export const getCacheStats = async (): Promise<StickerCacheStats> => {
  const stickers = await getAllCachedStickers();

  // 计算总大小（大约）
  let totalSize = 0;
  for (const sticker of stickers) {
    totalSize += sticker.imageData.length * 2; // base64 大约是原始的 4/3，UTF-16 每字符 2 字节
  }

  // 获取使用最多的贴纸
  const mostUsed = [...stickers]
    .sort((a, b) => b.usageCount - a.usageCount)
    .slice(0, 10);

  return {
    totalCached: stickers.length,
    totalSize,
    hitRate: 0, // 需要在运行时追踪
    mostUsed
  };
};

// 删除单个贴纸
export const deleteSticker = async (id: string): Promise<void> => {
  const database = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.delete(id);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

// 清空所有缓存
export const clearAllCache = async (): Promise<void> => {
  const database = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.clear();

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};
