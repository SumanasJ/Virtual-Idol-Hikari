import { MemoryFact, Relation } from '../types';

const DB_NAME = 'HikariMemoryDB';
const DB_VERSION = 1;
const FACTS_STORE = 'facts';
const RELATIONS_STORE = 'relations';

let db: IDBDatabase | null = null;

// 初始化 IndexedDB
export const initMemoryDB = (): Promise<IDBDatabase> => {
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

      // 创建记忆碎片存储
      if (!database.objectStoreNames.contains(FACTS_STORE)) {
        const factsStore = database.createObjectStore(FACTS_STORE, { keyPath: 'id' });
        factsStore.createIndex('type', 'type', { unique: false });
        factsStore.createIndex('category', 'category', { unique: false });
        factsStore.createIndex('timestamp', 'timestamp', { unique: false });
        factsStore.createIndex('importance', 'importance', { unique: false });
      }

      // 创建羁绊关系存储
      if (!database.objectStoreNames.contains(RELATIONS_STORE)) {
        const relationsStore = database.createObjectStore(RELATIONS_STORE, { keyPath: 'id' });
        relationsStore.createIndex('source', 'source', { unique: false });
        relationsStore.createIndex('target', 'target', { unique: false });
        relationsStore.createIndex('timestamp', 'timestamp', { unique: false });
      }
    };
  });
};

// 添加记忆碎片
export const addMemoryFact = async (fact: Omit<MemoryFact, 'id' | 'timestamp'>): Promise<MemoryFact> => {
  const database = await initMemoryDB();

  const newFact: MemoryFact = {
    ...fact,
    id: `fact-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date().toISOString()
  };

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([FACTS_STORE], 'readwrite');
    const store = transaction.objectStore(FACTS_STORE);
    const request = store.add(newFact);

    request.onsuccess = () => resolve(newFact);
    request.onerror = () => reject(request.error);
  });
};

// 获取所有记忆碎片
export const getAllMemoryFacts = async (): Promise<MemoryFact[]> => {
  const database = await initMemoryDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([FACTS_STORE], 'readonly');
    const store = transaction.objectStore(FACTS_STORE);
    const request = store.getAll();

    request.onsuccess = () => {
      const facts = request.result as MemoryFact[];
      // 按时间倒序排列
      resolve(facts.sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      ));
    };
    request.onerror = () => reject(request.error);
  });
};

// 获取短期记忆
export const getShortTermMemories = async (): Promise<MemoryFact[]> => {
  const database = await initMemoryDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([FACTS_STORE], 'readonly');
    const store = transaction.objectStore(FACTS_STORE);
    const index = store.index('type');
    const request = index.getAll('short_term');

    request.onsuccess = () => {
      const facts = request.result as MemoryFact[];
      resolve(facts.sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      ));
    };
    request.onerror = () => reject(request.error);
  });
};

// 获取长期记忆
export const getLongTermMemories = async (): Promise<MemoryFact[]> => {
  const database = await initMemoryDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([FACTS_STORE], 'readonly');
    const store = transaction.objectStore(FACTS_STORE);
    const index = store.index('type');
    const request = index.getAll('long_term');

    request.onsuccess = () => {
      const facts = request.result as MemoryFact[];
      resolve(facts.sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      ));
    };
    request.onerror = () => reject(request.error);
  });
};

// 更新记忆类型（短期→长期）
export const promoteToLongTerm = async (factId: string): Promise<void> => {
  const database = await initMemoryDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([FACTS_STORE], 'readwrite');
    const store = transaction.objectStore(FACTS_STORE);
    const getRequest = store.get(factId);

    getRequest.onsuccess = () => {
      const fact = getRequest.result as MemoryFact;
      if (fact && fact.type === 'short_term') {
        fact.type = 'long_term';
        store.put(fact);
      }
      resolve();
    };
    getRequest.onerror = () => reject(getRequest.error);
  });
};

// 批量提升到长期记忆
export const batchPromoteToLongTerm = async (factIds: string[]): Promise<void> => {
  for (const id of factIds) {
    await promoteToLongTerm(id);
  }
};

// 更新记忆内容
export const updateMemoryFact = async (factId: string, updates: Partial<MemoryFact>): Promise<void> => {
  const database = await initMemoryDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([FACTS_STORE], 'readwrite');
    const store = transaction.objectStore(FACTS_STORE);
    const getRequest = store.get(factId);

    getRequest.onsuccess = () => {
      const fact = getRequest.result as MemoryFact;
      if (fact) {
        const updated = { ...fact, ...updates };
        store.put(updated);
      }
      resolve();
    };
    getRequest.onerror = () => reject(getRequest.error);
  });
};

// 删除记忆碎片
export const deleteMemoryFact = async (factId: string): Promise<void> => {
  const database = await initMemoryDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([FACTS_STORE], 'readwrite');
    const store = transaction.objectStore(FACTS_STORE);
    const request = store.delete(factId);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

// 清空短期记忆（超过保留期限的）
export const cleanupOldShortTermMemories = async (maxAgeHours = 48): Promise<void> => {
  const database = await initMemoryDB();
  const cutoffTime = new Date(Date.now() - maxAgeHours * 60 * 60 * 1000).toISOString();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([FACTS_STORE], 'readwrite');
    const store = transaction.objectStore(FACTS_STORE);
    const index = store.index('type');
    const request = index.openCursor(IDBKeyRange.only('short_term'));

    request.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest).result;
      if (cursor) {
        const fact = cursor.value as MemoryFact;
        if (fact.timestamp < cutoffTime) {
          cursor.delete();
        }
        cursor.continue();
      } else {
        resolve();
      }
    };
    request.onerror = () => reject(request.error);
  });
};

// 添加羁绊关系
export const addRelation = async (relation: Omit<Relation, 'id' | 'timestamp'>): Promise<Relation> => {
  const database = await initMemoryDB();

  const newRelation: Relation = {
    ...relation,
    id: `rel-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date().toISOString()
  };

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([RELATIONS_STORE], 'readwrite');
    const store = transaction.objectStore(RELATIONS_STORE);
    const request = store.add(newRelation);

    request.onsuccess = () => resolve(newRelation);
    request.onerror = () => reject(request.error);
  });
};

// 获取所有羁绊关系
export const getAllRelations = async (): Promise<Relation[]> => {
  const database = await initMemoryDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([RELATIONS_STORE], 'readonly');
    const store = transaction.objectStore(RELATIONS_STORE);
    const request = store.getAll();

    request.onsuccess = () => {
      const relations = request.result as Relation[];
      resolve(relations.sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      ));
    };
    request.onerror = () => reject(request.error);
  });
};

// 删除羁绊关系
export const deleteRelation = async (relationId: string): Promise<void> => {
  const database = await initMemoryDB();

  return new Promise((resolve, reject) => {
    const transaction = database.transaction([RELATIONS_STORE], 'readwrite');
    const store = transaction.objectStore(RELATIONS_STORE);
    const request = store.delete(relationId);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

// 从 localStorage 迁移数据到 IndexedDB
export const migrateFromLocalStorage = async (): Promise<void> => {
  const savedMemory = localStorage.getItem('hikari_memory_v5');
  if (!savedMemory) return;

  try {
    const oldData = JSON.parse(savedMemory) as { facts: MemoryFact[], relations: Relation[] };

    // 迁移记忆碎片
    for (const fact of oldData.facts || []) {
      // 如果没有 type 字段，默认为短期记忆
      if (!fact.type) {
        fact.type = 'short_term';
        fact.importance = 0.5;
        fact.source = 'system';
      }
      await addMemoryFact(fact);
    }

    // 迁移羁绊关系
    for (const relation of oldData.relations || []) {
      await addRelation(relation);
    }

    // 清除旧数据
    localStorage.removeItem('hikari_memory_v5');
  } catch (error) {
    console.error('Migration failed:', error);
  }
};

// 获取记忆统计
export const getMemoryStats = async () => {
  const [allFacts, shortTerm, longTerm, relations] = await Promise.all([
    getAllMemoryFacts(),
    getShortTermMemories(),
    getLongTermMemories(),
    getAllRelations()
  ]);

  return {
    totalFacts: allFacts.length,
    shortTermCount: shortTerm.length,
    longTermCount: longTerm.length,
    relationsCount: relations.length
  };
};
