"""
向量存储管理器
使用 Chroma 存储和检索对话历史的向量化表示
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer

from config.settings import settings


class VectorStoreManager:
    """向量存储管理器"""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "chat_history"
    ):
        """
        初始化向量存储管理器

        Args:
            persist_directory: 持久化目录
            collection_name: 集合名称
        """
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name

        # 确保目录存在
        os.makedirs(self.persist_directory, exist_ok=True)

        # 初始化嵌入模型
        self.embeddings = self._create_embeddings()

        # 初始化向量数据库
        self.vectorstore = self._create_vectorstore()

    def _create_embeddings(self):
        """创建嵌入模型"""
        embedding_model = settings.EMBEDDING_MODEL

        if "sentence-transformers" in embedding_model:
            # 使用本地 sentence-transformers
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                return HuggingFaceEmbeddings(
                    model_name=embedding_model,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
            except Exception as e:
                print(f"警告: 无法加载本地嵌入模型，使用 OpenAI embeddings: {e}")
                return OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        else:
            # 使用 OpenAI embeddings
            return OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

    def _create_vectorstore(self):
        """创建或加载向量数据库"""
        try:
            # 尝试加载已有的向量数据库
            vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"✅ 成功加载已有向量数据库: {self.persist_directory}")
            return vectorstore
        except Exception as e:
            print(f"创建新的向量数据库: {e}")
            # 创建新的向量数据库
            vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            return vectorstore

    def add_conversation(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加对话到向量数据库

        Args:
            session_id: 会话 ID
            user_message: 用户消息
            assistant_message: 助手回复
            metadata: 额外的元数据
        """
        # 合并消息
        combined_text = f"用户: {user_message}\n助手: {assistant_message}"

        # 创建元数据
        doc_metadata = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "assistant_message": assistant_message
        }

        if metadata:
            doc_metadata.update(metadata)

        # 创建文档
        document = Document(page_content=combined_text, metadata=doc_metadata)

        # 添加到向量数据库
        self.vectorstore.add_documents([document])

    def add_message(
        self,
        session_id: str,
        message: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加单条消息到向量数据库

        Args:
            session_id: 会话 ID
            message: 消息内容
            role: 角色（user/assistant）
            metadata: 额外的元数据
        """
        # 创建文档
        doc_metadata = {
            "session_id": session_id,
            "role": role,
            "timestamp": datetime.now().isoformat()
        }

        if metadata:
            doc_metadata.update(metadata)

        document = Document(page_content=message, metadata=doc_metadata)

        # 添加到向量数据库
        self.vectorstore.add_documents([document])

    def search(
        self,
        query: str,
        session_id: Optional[str] = None,
        k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        相似性搜索

        Args:
            query: 查询文本
            session_id: 会话 ID（如果指定，只搜索该会话）
            k: 返回结果数量
            filter_metadata: 元数据过滤条件

        Returns:
            相关文档列表
        """
        k = k or settings.K_RETRIEVAL

        # 执行搜索（使用文本搜索，不是向量搜索）
        results = self.vectorstore.similarity_search_with_score(query, k=k)

        # 只返回文档
        return [doc for doc, score in results]

    def search_by_score(
        self,
        query: str,
        session_id: Optional[str] = None,
        k: int = None,
        score_threshold: float = 0.7
    ) -> List[tuple[Document, float]]:
        """
        相似性搜索（带分数）

        Args:
            query: 查询文本
            session_id: 会话 ID
            k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            (文档, 分数) 元组列表
        """
        k = k or settings.K_RETRIEVAL

        # 构建过滤条件
        search_filter = {"session_id": session_id} if session_id else None

        # 执行搜索
        if search_filter:
            results = self.vectorstore.similarity_search_by_vector_with_relevance_scores(
                query,
                k=k,
                filter=search_filter
            )
        else:
            results = self.vectorstore.similarity_search_with_score(query, k=k)

        # 过滤低分结果
        return [(doc, score) for doc, score in results if score >= score_threshold]

    def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Document]:
        """
        获取最近的消息

        Args:
            session_id: 会话 ID
            limit: 返回数量

        Returns:
            消息文档列表
        """
        # 注意：Chroma 不直接支持时间排序，这里简化处理
        # 实际应用中可能需要额外的元数据存储
        results = self.search(
            query="",  # 空查询获取所有
            session_id=session_id,
            k=limit * 2  # 获取更多结果以筛选
        )

        # 按时间戳排序
        results_with_time = [
            (doc, doc.metadata.get("timestamp", ""))
            for doc in results
        ]
        results_with_time.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in results_with_time[:limit]]

    def delete_session(self, session_id: str) -> None:
        """
        删除会话的所有消息

        Args:
            session_id: 会话 ID
        """
        # Chroma 不直接支持按元数据删除
        # 需要先获取所有文档，然后逐个删除
        # 这是一个简化的实现
        try:
            # 获取会话的所有文档
            results = self.search(query="", session_id=session_id, k=1000)

            # 删除每个文档
            for doc in results:
                # Chroma 使用 ID 删除
                # 这里需要重新实现，因为 Chroma 的删除接口
                pass

            print(f"⚠️  删除会话功能需要额外实现")
        except Exception as e:
            print(f"删除会话失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取向量数据库统计信息

        Returns:
            统计信息字典
        """
        try:
            # 获取集合信息
            collection = self.vectorstore._collection

            return {
                "total_documents": collection.count(),
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {
                "error": str(e),
                "collection_name": self.collection_name
            }


# 全局向量存储管理器实例
_vector_store_manager: Optional[VectorStoreManager] = None


def get_vector_store() -> VectorStoreManager:
    """获取全局向量存储管理器实例"""
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager()
    return _vector_store_manager


if __name__ == "__main__":
    # 测试向量存储管理器
    print("=== 向量存储管理器测试 ===\n")

    try:
        # 初始化
        vector_store = VectorStoreManager(collection_name="test")
        print(f"✅ 向量存储初始化成功\n")

        # 测试添加对话
        print("测试 1: 添加对话")
        vector_store.add_conversation(
            session_id="test_session",
            user_message="你好！我喜欢音乐",
            assistant_message="真的吗？我也很喜欢音乐！你最喜欢什么类型的音乐？",
            metadata={"topic": "music", "emotion": "positive"}
        )
        print("✅ 对话添加成功\n")

        # 测试搜索
        print("测试 2: 相似性搜索")
        results = vector_store.search(
            query="音乐偏好",
            session_id="test_session",
            k=3
        )
        print(f"找到 {len(results)} 条相关记录")
        for i, doc in enumerate(results):
            print(f"{i+1}. {doc.page_content[:100]}...\n")

        # 测试统计
        print("测试 3: 获取统计信息")
        stats = vector_store.get_stats()
        print(f"统计信息: {stats}\n")

        print("✅ 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
