
import React, { useState, useEffect, useRef } from 'react';
import { Message, MemoryFact, Relation, MemoryState, StickerCache, StickerCacheStats, ChatSession, OfflineEventSummary } from './types';
import { getChatResponse, generateSticker, extractMemoriesFromInteraction } from './services/gemini';
import { getAllCachedStickers, getCacheStats, deleteSticker, clearAllCache } from './services/stickerCache';
import { getAllSessions, createSession, getSession, updateSession, deleteSession, addMessageToSession } from './services/sessionManager';
import { generateOfflineEvents, shouldTriggerOfflineEvent, getTimeDifference } from './services/offlineEvents';
import {
  getAllMemoryFacts,
  getAllRelations,
  migrateFromLocalStorage,
  getMemoryStats,
  updateMemoryFact,
  deleteMemoryFact,
  promoteToLongTerm,
  getLongTermMemories,
  addRelation
} from './services/memoryManager';
import {
  recordConversationMemory,
  organizeMemories,
  organizeAndSummarizeLongTerm,
  shouldRecordMemory
} from './services/memoryProcessor';
import { generateOpeningTopic } from './services/topicGenerator';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [simulatedTime, setSimulatedTime] = useState(new Date().toISOString());
  const [memory, setMemory] = useState<MemoryState>({ facts: [], relations: [] });
  const [personality, setPersonality] = useState({
    cheerfulness: 0.8,
    gentleness: 0.6,
    energy: 0.9,
    curiosity: 0.7,
    empathy: 0.5
  });
  const [isTyping, setIsTyping] = useState(false);
  const [timeOffset, setTimeOffset] = useState('');
  const [activeTab, setActiveTab] = useState<'chat' | 'memory' | 'graph' | 'stickers' | 'sessions'>('chat');
  const [cachedStickers, setCachedStickers] = useState<StickerCache[]>([]);
  const [cacheStats, setCacheStats] = useState<StickerCacheStats | null>(null);

  // 会话管理相关 state
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [showSessionList, setShowSessionList] = useState(false);

  // 离线事件相关 state
  const [offlineSummary, setOfflineSummary] = useState<OfflineEventSummary | null>(null);
  const [showOfflineSummary, setShowOfflineSummary] = useState(false);

  // 对话轮次计数器（用于决定何时记录记忆）
  const [conversationRounds, setConversationRounds] = useState(0);

  // 记忆编辑相关 state
  const [editingFactId, setEditingFactId] = useState<string | null>(null);
  const [editingFactText, setEditingFactText] = useState('');

  // 上一次整理长期记忆的时间
  const [lastLongTermOrganize, setLastLongTermOrganize] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  // 根据重要性获取样式
  const getImportanceStyles = (importance?: number) => {
    if (!importance) return { level: '一般', color: 'gray', stars: 0, opacity: 'opacity-60' };
    if (importance >= 0.7) return { level: '重要', color: 'rose', stars: 3, opacity: 'opacity-100' };
    if (importance >= 0.4) return { level: '中等', color: 'amber', stars: 2, opacity: 'opacity-80' };
    return { level: '一般', color: 'gray', stars: 1, opacity: 'opacity-60' };
  };

  useEffect(() => {
    const initializeApp = async () => {
      // 从 IndexedDB 加载记忆
      try {
        await migrateFromLocalStorage(); // 先迁移旧数据
        const [facts, relations] = await Promise.all([
          getAllMemoryFacts(),
          getAllRelations()
        ]);
        setMemory({ facts, relations });
      } catch (error) {
        console.error('加载记忆失败:', error);
      }

      // 从 localStorage 加载时间和性格（这些仍用 localStorage）
      const savedTime = localStorage.getItem('hikari_time_v5');
      if (savedTime) setSimulatedTime(savedTime);
      const savedPers = localStorage.getItem('hikari_personality_v5');
      if (savedPers) setPersonality(JSON.parse(savedPers));

      // 加载上一次整理长期记忆的时间
      const lastOrganize = localStorage.getItem('hikari_last_organize');
      if (lastOrganize) setLastLongTermOrganize(lastOrganize);

      // 初始化会话系统
      await initializeSessions();
    };

    initializeApp();
  }, []);

  // 初始化会话系统，迁移旧数据
  const initializeSessions = async () => {
    const allSessions = await getAllSessions();

    if (allSessions.length === 0) {
      // 检查是否有旧的 localStorage 数据需要迁移
      const savedMsgs = localStorage.getItem('hikari_messages_v5');
      if (savedMsgs) {
        const oldMessages = JSON.parse(savedMsgs) as Message[];
        const newSession = await createSession(oldMessages[0]);
        await updateSession({ ...newSession, messages: oldMessages });
        setCurrentSessionId(newSession.id);
        setMessages(oldMessages);
        setConversationRounds(0); // 重置对话轮次计数
      } else {
        // 创建新会话并显示正在输入效果
        const newSession = await createSession();
        setCurrentSessionId(newSession.id);
        setMessages([]); // 清空消息
        setConversationRounds(0); // 重置对话轮次计数
        setIsTyping(true); // 显示正在输入动画

        // 在后台生成开场白
        try {
          const longTermMemories = await getLongTermMemories();
          const { topic } = await generateOpeningTopic(longTermMemories, personality);

          const greetingMsg: Message = {
            id: `greeting-${Date.now()}`,
            role: 'assistant',
            content: topic,
            timestamp: new Date().toISOString()
          };

          setIsTyping(false);
          setMessages([greetingMsg]);
          await updateSession({ ...newSession, messages: [greetingMsg] });
        } catch (error) {
          console.error('生成开场白失败:', error);
          const fallbackMsg: Message = {
            id: `fallback-${Date.now()}`,
            role: 'assistant',
            content: '呀吼！今天也是元气满满的一天呢~有什么想聊的吗？★',
            timestamp: new Date().toISOString()
          };
          setIsTyping(false);
          setMessages([fallbackMsg]);
          await updateSession({ ...newSession, messages: [fallbackMsg] });
        }
      }
    } else {
      // 加载最近的会话
      setCurrentSessionId(allSessions[0].id);
      setMessages(allSessions[0].messages);
      setConversationRounds(0); // 重置对话轮次计数
      if (allSessions[0].personality) {
        setPersonality(allSessions[0].personality);
      }
    }

    setSessions(await getAllSessions());
  };

  // 加载会话列表
  const loadSessions = async () => {
    const allSessions = await getAllSessions();
    setSessions(allSessions);
  };

  // 创建新会话
  const handleNewSession = async () => {
    // 先创建空会话并立即切换
    const newSession = await createSession();
    setCurrentSessionId(newSession.id);
    setMessages([]);
    setPersonality({
      cheerfulness: 0.8,
      gentleness: 0.6,
      energy: 0.9,
      curiosity: 0.7,
      empathy: 0.5
    });
    setConversationRounds(0); // 重置对话轮次计数
    setActiveTab('chat');
    await loadSessions();

    // 显示正在输入效果
    setIsTyping(true);

    // 在后台生成开场白
    try {
      const longTermMemories = await getLongTermMemories();
      const { topic } = await generateOpeningTopic(longTermMemories, personality);

      const greetingMsg: Message = {
        id: `greeting-${Date.now()}`,
        role: 'assistant',
        content: topic,
        timestamp: new Date().toISOString()
      };

      // 替换为实际消息
      setIsTyping(false);
      setMessages([greetingMsg]);
      await updateSession({ ...newSession, messages: [greetingMsg] });
    } catch (error) {
      console.error('生成开场白失败:', error);
      // 失败时使用默认问候
      const fallbackMsg: Message = {
        id: `fallback-${Date.now()}`,
        role: 'assistant',
        content: '呀吼！今天也是元气满满的一天呢~有什么想聊的吗？★',
        timestamp: new Date().toISOString()
      };
      setIsTyping(false);
      setMessages([fallbackMsg]);
      await updateSession({ ...newSession, messages: [fallbackMsg] });
    }
  };

  // 切换会话
  const handleSwitchSession = async (sessionId: string) => {
    const session = await getSession(sessionId);
    if (!session) return;

    setCurrentSessionId(sessionId);
    setMessages(session.messages);
    if (session.personality) {
      setPersonality(session.personality);
    }
    setConversationRounds(0); // 重置对话轮次计数
    setActiveTab('chat');
    setShowSessionList(false);

    // 检查是否需要触发离线事件（至少离开2小时）
    if (session.lastVisitTime && shouldTriggerOfflineEvent(session.lastVisitTime, 2)) {
      const hoursPassed = getTimeDifference(session.lastVisitTime);
      const lastMsg = session.messages.length > 0
        ? session.messages[session.messages.length - 1].content
        : undefined;

      const summary = await generateOfflineEvents(hoursPassed, lastMsg, session.personality);
      setOfflineSummary(summary);
      setShowOfflineSummary(true);

      // 添加打招呼消息
      const greetingMsg: Message = {
        id: `offline-${Date.now()}`,
        role: 'assistant',
        content: summary.greeting,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, greetingMsg]);
    }

    // 更新最后访问时间
    session.lastVisitTime = new Date().toISOString();
    await updateSession(session);
    await loadSessions();
  };

  // 删除会话
  const handleDeleteSession = async (sessionId: string) => {
    if (confirm('确定要删除这个会话吗？')) {
      await deleteSession(sessionId);

      // 如果删除的是当前会话，切换到其他会话
      if (sessionId === currentSessionId) {
        const remainingSessions = sessions.filter(s => s.id !== sessionId);
        if (remainingSessions.length > 0) {
          await handleSwitchSession(remainingSessions[0].id);
        } else {
          await handleNewSession();
        }
      }

      await loadSessions();
    }
  };

  // 重命名会话
  const handleRenameSession = async (sessionId: string, newTitle: string) => {
    const session = await getSession(sessionId);
    if (!session) return;

    session.title = newTitle;
    await updateSession(session);
    await loadSessions();
  };

  // 获取事件类型图标
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'activity': return 'fa-music';
      case 'message': return 'fa-envelope';
      case 'thought': return 'fa-heart';
      case 'discovery': return 'fa-star';
      default: return 'fa-circle';
    }
  };

  // 获取情绪颜色
  const getEventIconColor = (emotion: string) => {
    switch (emotion) {
      case 'happy': return 'text-pink-400';
      case 'excited': return 'text-purple-400';
      case 'thoughtful': return 'text-blue-400';
      case 'curious': return 'text-green-400';
      case 'missed': return 'text-rose-400';
      case 'surprised': return 'text-amber-400';
      default: return 'text-gray-400';
    }
  };

  // 处理记忆编辑
  const handleEditFact = (fact: MemoryFact) => {
    setEditingFactId(fact.id);
    setEditingFactText(fact.fact);
  };

  const handleSaveFact = async () => {
    if (!editingFactId || !editingFactText.trim()) return;

    await updateMemoryFact(editingFactId, { fact: editingFactText.trim() });

    // 重新加载记忆
    const [updatedFacts, updatedRelations] = await Promise.all([
      getAllMemoryFacts(),
      getAllRelations()
    ]);
    setMemory({ facts: updatedFacts, relations: updatedRelations });

    setEditingFactId(null);
    setEditingFactText('');
  };

  const handleCancelEdit = () => {
    setEditingFactId(null);
    setEditingFactText('');
  };

  const handleDeleteFact = async (factId: string) => {
    if (!confirm('确定要删除这条记忆吗？')) return;

    await deleteMemoryFact(factId);

    // 重新加载记忆
    const [updatedFacts, updatedRelations] = await Promise.all([
      getAllMemoryFacts(),
      getAllRelations()
    ]);
    setMemory({ facts: updatedFacts, relations: updatedRelations });
  };

  const handlePromoteFact = async (factId: string) => {
    await promoteToLongTerm(factId);

    // 重新加载记忆
    const [updatedFacts, updatedRelations] = await Promise.all([
      getAllMemoryFacts(),
      getAllRelations()
    ]);
    setMemory({ facts: updatedFacts, relations: updatedRelations });
  };

  // 批量提升所有短期记忆到长期
  const handlePromoteAllShortTerm = async () => {
    if (!confirm('确定要将所有短期记忆提升为长期记忆吗？')) return;

    const shortTermFacts = memory.facts.filter(f => f.type === 'short_term');
    for (const fact of shortTermFacts) {
      await promoteToLongTerm(fact.id);
    }

    // 重新加载记忆
    const [updatedFacts, updatedRelations] = await Promise.all([
      getAllMemoryFacts(),
      getAllRelations()
    ]);
    setMemory({ facts: updatedFacts, relations: updatedRelations });
  };

  // 保存时间到 localStorage（跨会话共享）
  useEffect(() => {
    localStorage.setItem('hikari_time_v5', simulatedTime);
  }, [simulatedTime]);

  // 保存当前会话
  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      updateSession({
        id: currentSessionId,
        title: sessions.find(s => s.id === currentSessionId)?.title || '新对话',
        messages,
        createdAt: sessions.find(s => s.id === currentSessionId)?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        personality
      }).catch(console.error);
    }
  }, [messages, personality, currentSessionId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isTyping]);

  useEffect(() => {
    if (activeTab === 'stickers') {
      loadCacheData();
    }
  }, [activeTab]);

  const loadCacheData = async () => {
    const stickers = await getAllCachedStickers();
    const stats = await getCacheStats();
    setCachedStickers(stickers.sort((a, b) => b.usageCount - a.usageCount));
    setCacheStats(stats);
  };

  const handleDeleteSticker = async (id: string) => {
    if (confirm('确定要删除这个贴纸吗？')) {
      await deleteSticker(id);
      loadCacheData();
    }
  };

  const handleClearAllCache = async () => {
    if (confirm('确定要清空所有缓存吗？这不会删除已生成的图片，但下次需要重新生成。')) {
      await clearAllCache();
      loadCacheData();
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    // 如果没有当前会话，创建新会话
    let sessionId = currentSessionId;
    if (!sessionId) {
      const newSession = await createSession();
      sessionId = newSession.id;
      setCurrentSessionId(sessionId);
      await loadSessions();
    }

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: simulatedTime
    };

    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setIsTyping(true);

    // 只传递长期记忆（偏好、理解、重要事实），限制数量以降低依赖
    const longTermFacts = memory.facts.filter(f => f.type === 'long_term');
    const topFacts = longTermFacts
      .sort((a, b) => (b.importance || 0.5) - (a.importance || 0.5))
      .slice(0, 5); // 只取最重要的5条

    const relevantFactsStr = topFacts.length > 0
      ? topFacts.map(f => `- ${f.fact}`).join('\n')
      : ""; // 如果没有长期记忆，传空字符串而不是显示所有记忆

    const result = await getChatResponse(
      currentInput,
      messages.slice(-8).map(m => ({ role: m.role, content: m.content })),
      relevantFactsStr,
      new Date(simulatedTime).toLocaleString(),
      personality
    );

    if (result.personality_impact) {
      setPersonality(prev => {
        const next = { ...prev };
        Object.keys(result.personality_impact).forEach((key) => {
          (next as any)[key] = Math.max(0, Math.min(1, (next as any)[key] + (result.personality_impact[key] || 0)));
        });
        return next;
      });
    }

    let fullResponseText = "";
    for (let i = 0; i < result.segments.length; i++) {
      const segment = result.segments[i];
      fullResponseText += segment + " ";
      const botMsg: Message = {
        id: `b-${Date.now()}-${i}`,
        role: 'assistant',
        content: segment,
        timestamp: simulatedTime
      };
      setMessages(prev => [...prev, botMsg]);
      if (result.segments.length > 1) {
        await new Promise(r => setTimeout(r, 600 + Math.random() * 400));
      }
    }

    if (result.stickerRequest) {
      const stickerUrl = await generateSticker(result.stickerRequest);
      if (stickerUrl) {
        setMessages(prev => [...prev, {
          id: `s-${Date.now()}`,
          role: 'assistant',
          content: `${result.stickerRequest.detail}`,
          imageUrl: stickerUrl,
          timestamp: simulatedTime
        }]);
      }
    }

    setIsTyping(false);

    // 增加对话轮次计数
    const nextRound = conversationRounds + 1;
    setConversationRounds(nextRound);

    // 每轮对话都更新羁绊图（提取实体和关系）
    try {
      const extracted = await extractMemoriesFromInteraction(currentInput, fullResponseText, simulatedTime);

      // 添加提取到的关系
      if (extracted.relationships && extracted.relationships.length > 0) {
        for (const rel of extracted.relationships) {
          await addRelation({
            source: rel.source,
            predicate: rel.type, // API返回的是type字段
            target: rel.target
          });
        }
        console.log(`🔗 添加了 ${extracted.relationships.length} 条羁绊关系`);
      }
    } catch (error) {
      console.error('提取羁绊关系失败:', error);
    }

    // 记录记忆到短期存储（每轮都记录，去重逻辑在内部）
    await recordConversationMemory(currentInput, fullResponseText, simulatedTime);

    // 重新加载记忆和关系（每次对话后都更新UI）
    const [updatedFacts, updatedRelations] = await Promise.all([
      getAllMemoryFacts(),
      getAllRelations()
    ]);
    setMemory({ facts: updatedFacts, relations: updatedRelations });

    // 检查是否需要整理记忆
    const now = new Date();
    const hoursSinceLastOrganize = lastLongTermOrganize
      ? (now.getTime() - new Date(lastLongTermOrganize).getTime()) / (60 * 60 * 1000)
      : 999;

    const [facts, relations] = await Promise.all([
      getAllMemoryFacts(),
      getAllRelations()
    ]);

    const shortTermCount = facts.filter(f => f.type === 'short_term').length;
    const longTermCount = facts.filter(f => f.type === 'long_term').length;

    // 短期记忆达到8条立即整理，或超过6小时且短期记忆>=5条，或长期记忆>=20条
    const shouldOrganizeNow =
      shortTermCount >= 8 ||
      (hoursSinceLastOrganize > 6 && shortTermCount >= 5) ||
      longTermCount >= 20;

    if (shouldOrganizeNow) {
      console.log('📚 整理记忆中...');
      const { promoted, summarized } = await organizeAndSummarizeLongTerm();
      console.log(`✅ 提升 ${promoted} 条到长期记忆，总结 ${summarized} 条核心记忆`);

      // 更新整理时间（每次整理后都更新）
      setLastLongTermOrganize(now.toISOString());
      localStorage.setItem('hikari_last_organize', now.toISOString());

      // 重新加载记忆
      const [updatedFacts, updatedRelations] = await Promise.all([
        getAllMemoryFacts(),
        getAllRelations()
      ]);
      setMemory({ facts: updatedFacts, relations: updatedRelations });
    }
  };

  const adjustTime = () => {
    if (!timeOffset) return;
    const date = new Date(simulatedTime);
    const num = parseInt(timeOffset);
    if (isNaN(num)) return;
    if (timeOffset.includes('hour')) date.setHours(date.getHours() + num);
    else date.setDate(date.getDate() + num);
    setSimulatedTime(date.toISOString());
    setTimeOffset('');
  };

  const clearMemory = () => {
    if (confirm("真的要重置所有记忆吗？光酱会忘记你的哦...")) {
      localStorage.clear();
      window.location.reload();
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-5xl mx-auto bg-white shadow-2xl overflow-hidden font-sans border-x border-pink-100">
      <header className="bg-gradient-to-r from-pink-400 to-rose-400 text-white p-5 flex justify-between items-center shadow-md relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-10 rotate-12 scale-150">
           <i className="fas fa-music text-8xl"></i>
        </div>
        <div className="flex items-center gap-4 relative z-10">
          <div className="w-14 h-14 rounded-full border-4 border-white shadow-inner bg-pink-100 flex items-center justify-center overflow-hidden">
            <i className="fas fa-star text-pink-500 text-2xl animate-pulse"></i>
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight flex items-center gap-2">
              星野光 <span className="text-[10px] bg-white text-pink-500 px-3 py-1 rounded-full font-bold shadow-sm">IDOL</span>
            </h1>
            <p className="text-xs opacity-90 font-bold italic">"和粉丝君创造最棒的回忆！★"</p>
          </div>
        </div>
        <div className="flex items-center gap-4 relative z-10">
          <button onClick={handleNewSession} className="bg-white/20 hover:bg-white/30 backdrop-blur-sm px-4 py-2 rounded-xl text-xs font-black flex items-center gap-2 transition-all border border-white/30">
            <i className="fas fa-plus"></i> 新会话
          </button>
          <div className="bg-black/10 backdrop-blur-md p-2 rounded-xl border border-white/20">
            <div className="text-[10px] uppercase font-black tracking-widest opacity-70">Osaka Local Time</div>
            <div className="text-sm font-mono font-bold">
               {new Date(simulatedTime).toLocaleDateString()} {new Date(simulatedTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 border-r border-pink-50 bg-white p-4 flex flex-col gap-6">
          <div className="p-3 bg-pink-50 rounded-2xl border border-pink-100">
            <label className="block text-[10px] font-black text-pink-400 uppercase mb-2 tracking-widest">Time Leap</label>
            <div className="flex gap-2">
              <input type="text" placeholder="+3 days" value={timeOffset} onChange={e => setTimeOffset(e.target.value)} className="flex-1 text-xs border border-pink-100 rounded-lg px-2 py-2 outline-none" onKeyDown={e => e.key === 'Enter' && adjustTime()} />
              <button onClick={adjustTime} className="bg-pink-400 text-white p-2 rounded-lg"><i className="fas fa-bolt"></i></button>
            </div>
          </div>

          <nav className="flex flex-col gap-2 mt-2">
            <button onClick={() => setActiveTab('chat')} className={`flex items-center gap-4 px-5 py-3 rounded-2xl text-sm transition-all ${activeTab === 'chat' ? 'bg-pink-400 text-white font-black shadow-lg' : 'text-gray-500 hover:bg-pink-50'}`}>
              <i className="fas fa-comment-heart"></i> 对话
            </button>
            <button onClick={() => setActiveTab('memory')} className={`flex items-center gap-4 px-5 py-3 rounded-2xl text-sm transition-all ${activeTab === 'memory' ? 'bg-pink-400 text-white font-black shadow-lg' : 'text-gray-500 hover:bg-pink-50'}`}>
              <i className="fas fa-stars"></i> 记忆碎片
            </button>
            <button onClick={() => setActiveTab('graph')} className={`flex items-center gap-4 px-5 py-3 rounded-2xl text-sm transition-all ${activeTab === 'graph' ? 'bg-pink-400 text-white font-black shadow-lg' : 'text-gray-500 hover:bg-pink-50'}`}>
              <i className="fas fa-dna"></i> 羁绊图
            </button>
            <button onClick={() => setActiveTab('stickers')} className={`flex items-center gap-4 px-5 py-3 rounded-2xl text-sm transition-all ${activeTab === 'stickers' ? 'bg-pink-400 text-white font-black shadow-lg' : 'text-gray-500 hover:bg-pink-50'}`}>
              <i className="fas fa-images"></i> 贴纸库
            </button>
            <button onClick={() => setActiveTab('sessions')} className={`flex items-center gap-4 px-5 py-3 rounded-2xl text-sm transition-all ${activeTab === 'sessions' ? 'bg-pink-400 text-white font-black shadow-lg' : 'text-gray-500 hover:bg-pink-50'}`}>
              <i className="fas fa-history"></i> 历史会话
            </button>
          </nav>

          <button onClick={clearMemory} className="mt-auto p-4 text-[10px] text-gray-300 hover:text-rose-400 font-black uppercase text-center border-t border-pink-50">Reset World</button>
        </aside>

        <main className="flex-1 flex flex-col relative bg-slate-50/50">
          {activeTab === 'chat' && (
            <>
              <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar bg-[url('https://www.transparenttextures.com/patterns/grid-me.png')]">
                {messages.length === 0 && (
                  <div className="text-center py-20 flex flex-col items-center">
                    <div className="w-20 h-20 bg-white rounded-full shadow-xl flex items-center justify-center text-pink-300 mb-6 border-4 border-pink-100">
                      <i className="fas fa-microphone-alt text-3xl animate-bounce"></i>
                    </div>
                    <h2 className="text-xl font-black text-gray-800">呀吼！粉丝君~！✨</h2>
                    <p className="text-xs text-gray-400 font-bold mt-2 tracking-widest uppercase">Start a conversation with Hikari</p>
                  </div>
                )}
                {messages.map((m) => (
                  <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}>
                    <div className={`max-w-[85%] relative ${
                      m.role === 'user' 
                        ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl rounded-tr-none shadow-sm' 
                        : 'bg-white text-gray-800 rounded-2xl rounded-tl-none border border-pink-100 shadow-sm'
                    } px-5 py-3`}>
                      {m.imageUrl ? (
                        <div className="flex flex-col items-center gap-3 py-1">
                           <img src={m.imageUrl} alt="Sticker" className="w-40 h-40 object-contain rounded-xl bg-pink-50/30 p-1" />
                           <span className="text-[10px] font-black text-pink-400 bg-pink-50 px-3 py-0.5 rounded-full uppercase tracking-tighter">★ {m.content} ★</span>
                        </div>
                      ) : (
                        <p className="text-sm leading-relaxed font-medium">{m.content}</p>
                      )}
                      <div className={`text-[8px] mt-1 font-bold opacity-30 ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
                        {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                ))}

                {/* 离线事件摘要展示 */}
                {showOfflineSummary && offlineSummary && (
                  <div className="flex justify-start">
                    <div className="max-w-[85%] bg-gradient-to-br from-pink-50 to-rose-50 text-gray-800 rounded-2xl rounded-tl-none border-2 border-pink-200 shadow-sm overflow-hidden">
                      <div className="bg-gradient-to-r from-pink-400 to-rose-400 text-white px-4 py-2 flex items-center justify-between">
                        <span className="text-xs font-black flex items-center gap-2">
                          <i className="fas fa-clock"></i>
                          离开 {offlineSummary.timePassed}
                        </span>
                        <button
                          onClick={() => setShowOfflineSummary(false)}
                          className="text-white/80 hover:text-white"
                        >
                          <i className="fas fa-times"></i>
                        </button>
                      </div>
                      <div className="p-4 space-y-3">
                        {offlineSummary.events.map((event, idx) => (
                          <div key={event.id || idx} className="flex items-start gap-3 text-xs">
                            <div className={`mt-0.5 ${getEventIconColor(event.emotion)}`}>
                              <i className={`fas ${getEventIcon(event.type)}`}></i>
                            </div>
                            <div className="flex-1">
                              <div className="font-bold text-gray-700">{event.title}</div>
                              {event.description && (
                                <div className="text-gray-500 mt-0.5 leading-relaxed">{event.description}</div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-pink-100 rounded-2xl rounded-tl-none px-4 py-2 shadow-sm flex gap-1">
                      <div className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                      <div className="w-1.5 h-1.5 bg-pink-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                    </div>
                  </div>
                )}
              </div>
              <div className="p-6 bg-white border-t border-pink-50">
                <div className="flex gap-3">
                  <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} placeholder="跟光聊聊天吧...~" className="flex-1 bg-gray-50 rounded-2xl px-6 py-4 outline-none border-2 border-transparent focus:border-pink-300 focus:bg-white transition-all text-sm font-medium shadow-inner" />
                  <button onClick={handleSend} disabled={!input.trim() || isTyping} className="bg-pink-400 text-white w-14 h-14 rounded-2xl flex items-center justify-center hover:shadow-lg transition-all disabled:opacity-50">
                    <i className="fas fa-paper-plane text-lg"></i>
                  </button>
                </div>
              </div>
            </>
          )}

          {activeTab === 'memory' && (
            <div className="flex-1 overflow-y-auto p-8">
              <div className="max-w-2xl mx-auto space-y-4">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-black text-gray-800 flex items-center gap-2">
                    <i className="fas fa-stars text-pink-400"></i> 光的小本本
                  </h2>
                  <div className="flex gap-2">
                    {memory.facts.filter(f => f.type === 'short_term').length > 0 && (
                      <button onClick={handlePromoteAllShortTerm} className="text-xs bg-amber-100 text-amber-600 px-3 py-1.5 rounded-lg font-black hover:bg-amber-200">
                        <i className="fas fa-arrow-up mr-1"></i>全部提升
                      </button>
                    )}
                  </div>
                </div>

                {memory.facts.length === 0 ? (
                  <p className="text-gray-400 text-center py-20 italic">还没有特别的回忆呢...~</p>
                ) : (
                  <>
                    {/* 短期记忆 */}
                    {memory.facts.filter(f => f.type === 'short_term').length > 0 && (
                      <div className="mb-6">
                        <h3 className="text-sm font-black text-amber-500 mb-3 flex items-center gap-2">
                          <i className="fas fa-clock"></i> 短期记忆 ({memory.facts.filter(f => f.type === 'short_term').length})
                        </h3>
                        <div className="space-y-2">
                          {memory.facts.filter(f => f.type === 'short_term').map(f => {
                            const importanceStyle = getImportanceStyles(f.importance);
                            return (
                            <div key={f.id} className={`group bg-amber-50 p-4 rounded-xl border-l-4 ${f.category === 'hikari_info' ? 'border-indigo-400' : 'border-amber-400'} shadow-sm hover:shadow-md transition-all ${importanceStyle.opacity}`}>
                              {editingFactId === f.id ? (
                                <div className="space-y-2">
                                  <input
                                    type="text"
                                    value={editingFactText}
                                    onChange={(e) => setEditingFactText(e.target.value)}
                                    className="w-full px-3 py-2 text-sm border border-amber-300 rounded-lg focus:outline-none focus:border-amber-500"
                                    autoFocus
                                  />
                                  <div className="flex gap-2">
                                    <button onClick={handleSaveFact} className="text-xs bg-green-500 text-white px-3 py-1 rounded-lg font-black">
                                      <i className="fas fa-check mr-1"></i>保存
                                    </button>
                                    <button onClick={handleCancelEdit} className="text-xs bg-gray-300 text-gray-600 px-3 py-1 rounded-lg font-black">
                                      <i className="fas fa-times mr-1"></i>取消
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <>
                                  <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-2">
                                      <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${f.category === 'hikari_info' ? 'bg-indigo-50 text-indigo-500' : 'bg-amber-100 text-amber-600'}`}>
                                        {f.category}
                                      </span>
                                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full bg-${importanceStyle.color}-100 text-${importanceStyle.color}-600`}>
                                        {importanceStyle.level}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                      <button onClick={() => handleEditFact(f)} className="text-[10px] text-blue-400 hover:text-blue-600 px-2 py-1">
                                        <i className="fas fa-edit"></i>
                                      </button>
                                      <button onClick={() => handlePromoteFact(f.id)} className="text-[10px] text-green-400 hover:text-green-600 px-2 py-1" title="提升为长期记忆">
                                        <i className="fas fa-arrow-up"></i>
                                      </button>
                                      <button onClick={() => handleDeleteFact(f.id)} className="text-[10px] text-rose-400 hover:text-rose-600 px-2 py-1">
                                        <i className="fas fa-trash"></i>
                                      </button>
                                    </div>
                                  </div>
                                  <div className="flex justify-between items-center mb-2">
                                    <p className="text-sm font-bold text-gray-700 leading-relaxed flex-1">{f.fact}</p>
                                    <div className="flex items-center gap-2 ml-2">
                                      {f.importance && (
                                        <span className="text-[8px] text-amber-400 shrink-0">
                                          {'⭐'.repeat(Math.ceil(f.importance * 3))}
                                        </span>
                                      )}
                                      <span className="text-[10px] text-gray-400 font-mono shrink-0">
                                        {new Date(f.timestamp).toLocaleDateString()} {new Date(f.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                      </span>
                                    </div>
                                  </div>
                                </>
                              )}
                            </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* 长期记忆 */}
                    {memory.facts.filter(f => f.type === 'long_term').length > 0 && (
                      <div>
                        <h3 className="text-sm font-black text-pink-500 mb-3 flex items-center gap-2">
                          <i className="fas fa-heart"></i> 长期记忆 ({memory.facts.filter(f => f.type === 'long_term').length})
                        </h3>
                        <div className="space-y-2">
                          {memory.facts.filter(f => f.type === 'long_term').map(f => {
                            const importanceStyle = getImportanceStyles(f.importance);
                            return (
                            <div key={f.id} className={`group bg-gradient-to-br from-pink-50 to-rose-50 p-5 rounded-2xl border-l-4 ${f.category === 'hikari_info' ? 'border-indigo-400' : 'border-pink-400'} shadow-sm hover:shadow-md transition-all ${importanceStyle.opacity}`}>
                              {editingFactId === f.id ? (
                                <div className="space-y-2">
                                  <input
                                    type="text"
                                    value={editingFactText}
                                    onChange={(e) => setEditingFactText(e.target.value)}
                                    className="w-full px-3 py-2 text-sm border border-pink-300 rounded-lg focus:outline-none focus:border-pink-500"
                                    autoFocus
                                  />
                                  <div className="flex gap-2">
                                    <button onClick={handleSaveFact} className="text-xs bg-green-500 text-white px-3 py-1 rounded-lg font-black">
                                      <i className="fas fa-check mr-1"></i>保存
                                    </button>
                                    <button onClick={handleCancelEdit} className="text-xs bg-gray-300 text-gray-600 px-3 py-1 rounded-lg font-black">
                                      <i className="fas fa-times mr-1"></i>取消
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <>
                                  <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-2">
                                      <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${f.category === 'hikari_info' ? 'bg-indigo-50 text-indigo-500' : 'bg-pink-50 text-pink-500'}`}>
                                        {f.category}
                                      </span>
                                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full bg-${importanceStyle.color}-100 text-${importanceStyle.color}-600`}>
                                        {importanceStyle.level}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                      <button onClick={() => handleEditFact(f)} className="text-[10px] text-blue-400 hover:text-blue-600 px-2 py-1">
                                        <i className="fas fa-edit"></i>
                                      </button>
                                      <button onClick={() => handleDeleteFact(f.id)} className="text-[10px] text-rose-400 hover:text-rose-600 px-2 py-1">
                                        <i className="fas fa-trash"></i>
                                      </button>
                                    </div>
                                  </div>
                                  <div className="flex justify-between items-center mb-2">
                                    <p className="text-sm font-bold text-gray-700 leading-relaxed flex-1">{f.fact}</p>
                                    <div className="flex items-center gap-2 ml-2">
                                      {f.importance && (
                                        <span className="text-[8px] text-pink-400 shrink-0">
                                          {'⭐'.repeat(Math.ceil(f.importance * 3))}
                                        </span>
                                      )}
                                      <span className="text-[10px] text-gray-400 font-mono shrink-0">
                                        {new Date(f.timestamp).toLocaleDateString()} {new Date(f.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                      </span>
                                    </div>
                                  </div>
                                </>
                              )}
                            </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {activeTab === 'graph' && (
            <div className="flex-1 overflow-y-auto p-8">
               <div className="max-w-4xl mx-auto">
                <h2 className="text-xl font-black text-gray-800 mb-8 flex items-center gap-2"><i className="fas fa-project-diagram text-pink-400"></i> 羁绊图谱</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {memory.relations.length === 0 ? <p className="text-gray-300 italic text-center col-span-full py-20">羁绊还在建立中...~</p> :
                    memory.relations.map(r => (
                      <div key={r.id} className="bg-white p-6 rounded-3xl border border-pink-100 shadow-sm flex flex-col items-center text-center hover:scale-105 transition-transform duration-300">
                        <div className="text-xs font-black text-white bg-indigo-500 px-3 py-1.5 rounded-xl min-w-[80px]">{r.source}</div>
                        <div className="my-2 text-[10px] font-black text-pink-400 flex flex-col items-center">
                          <div className="w-0.5 h-3 bg-pink-100"></div>
                          <span className="my-1 px-2 py-1 bg-pink-50 rounded-lg">{r.predicate}</span>
                          <div className="w-0.5 h-3 bg-pink-100"></div>
                        </div>
                        <div className="text-xs font-black text-gray-700 bg-white border border-pink-100 px-3 py-1.5 rounded-xl min-w-[80px]">{r.target}</div>
                      </div>
                    ))
                  }
                </div>
              </div>
            </div>
          )}

          {activeTab === 'stickers' && (
            <div className="flex-1 overflow-y-auto p-8">
              <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                  <h2 className="text-xl font-black text-gray-800 flex items-center gap-2">
                    <i className="fas fa-images text-pink-400"></i> 贴纸缓存库
                  </h2>
                  <button onClick={handleClearAllCache} className="text-xs bg-rose-100 text-rose-600 px-4 py-2 rounded-xl font-black hover:bg-rose-200 transition-all">
                    <i className="fas fa-trash-alt mr-2"></i>清空缓存
                  </button>
                </div>

                {cacheStats && (
                  <div className="grid grid-cols-3 gap-4 mb-8">
                    <div className="bg-gradient-to-br from-pink-50 to-rose-50 p-5 rounded-2xl border border-pink-100">
                      <div className="text-[10px] font-black text-pink-400 uppercase tracking-widest mb-1">缓存数量</div>
                      <div className="text-2xl font-black text-gray-800">{cacheStats.totalCached}</div>
                    </div>
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-5 rounded-2xl border border-blue-100">
                      <div className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-1">总大小</div>
                      <div className="text-2xl font-black text-gray-800">{(cacheStats.totalSize / 1024 / 1024).toFixed(2)} MB</div>
                    </div>
                    <div className="bg-gradient-to-br from-amber-50 to-yellow-50 p-5 rounded-2xl border border-amber-100">
                      <div className="text-[10px] font-black text-amber-400 uppercase tracking-widest mb-1">最多使用</div>
                      <div className="text-2xl font-black text-gray-800">{cacheStats.mostUsed[0]?.usageCount || 0} 次</div>
                    </div>
                  </div>
                )}

                {cachedStickers.length === 0 ? (
                  <div className="text-center py-20">
                    <div className="w-20 h-20 bg-gray-100 rounded-full shadow-xl flex items-center justify-center text-gray-300 mb-6 mx-auto">
                      <i className="fas fa-images text-3xl"></i>
                    </div>
                    <h3 className="text-lg font-black text-gray-600">还没有缓存的贴纸~</h3>
                    <p className="text-xs text-gray-400 mt-2">生成的贴纸会自动缓存到这里</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {cachedStickers.map((sticker) => (
                      <div key={sticker.id} className="group relative bg-white rounded-2xl border border-pink-100 p-3 hover:shadow-lg transition-all hover:scale-105">
                        <div className="aspect-square bg-pink-50 rounded-xl overflow-hidden mb-2">
                          <img src={sticker.imageData} alt={sticker.detail} className="w-full h-full object-contain" />
                        </div>
                        <div className="text-[10px] font-black text-gray-600 truncate">{sticker.detail}</div>
                        <div className="flex justify-between items-center mt-1">
                          <span className="text-[8px] text-gray-400">{sticker.usageCount}次</span>
                          <button
                            onClick={() => handleDeleteSticker(sticker.id)}
                            className="text-[8px] text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity hover:text-rose-600"
                          >
                            <i className="fas fa-times"></i>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'sessions' && (
            <div className="flex-1 overflow-y-auto p-8">
              <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                  <h2 className="text-xl font-black text-gray-800 flex items-center gap-2">
                    <i className="fas fa-history text-pink-400"></i> 历史会话
                  </h2>
                  <button onClick={handleNewSession} className="text-xs bg-pink-400 text-white px-4 py-2 rounded-xl font-black hover:bg-pink-500 transition-all">
                    <i className="fas fa-plus mr-2"></i>新建会话
                  </button>
                </div>

                {sessions.length === 0 ? (
                  <div className="text-center py-20">
                    <div className="w-20 h-20 bg-gray-100 rounded-full shadow-xl flex items-center justify-center text-gray-300 mb-6 mx-auto">
                      <i className="fas fa-comments text-3xl"></i>
                    </div>
                    <h3 className="text-lg font-black text-gray-600">还没有历史会话~</h3>
                    <p className="text-xs text-gray-400 mt-2">开始一段新的对话吧</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {sessions.map((session) => (
                      <div
                        key={session.id}
                        className={`group bg-white rounded-2xl border-2 p-5 transition-all hover:shadow-lg ${
                          session.id === currentSessionId
                            ? 'border-pink-400 shadow-md'
                            : 'border-pink-100 hover:border-pink-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              {session.id === currentSessionId && (
                                <span className="text-[10px] bg-pink-400 text-white px-2 py-0.5 rounded-full font-black">
                                  当前
                                </span>
                              )}
                              <input
                                type="text"
                                value={session.title}
                                onChange={(e) => handleRenameSession(session.id, e.target.value)}
                                className="text-sm font-black text-gray-800 bg-transparent border-none outline-none flex-1"
                                onClick={(e) => e.stopPropagation()}
                              />
                            </div>
                            <div className="text-[10px] text-gray-400 font-mono">
                              {session.messages.length} 条消息 · 更新于 {new Date(session.updatedAt).toLocaleString()}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => handleSwitchSession(session.id)}
                              className="text-xs bg-pink-100 text-pink-600 px-3 py-1.5 rounded-lg font-black hover:bg-pink-200"
                            >
                              <i className="fas fa-external-link-alt mr-1"></i>打开
                            </button>
                            <button
                              onClick={() => handleDeleteSession(session.id)}
                              className="text-xs bg-rose-100 text-rose-600 px-3 py-1.5 rounded-lg font-black hover:bg-rose-200"
                            >
                              <i className="fas fa-trash"></i>
                            </button>
                          </div>
                        </div>
                        <div className="mt-3 text-xs text-gray-500 line-clamp-2">
                          {session.messages.length > 0 ? session.messages[0].content : '空会话'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
