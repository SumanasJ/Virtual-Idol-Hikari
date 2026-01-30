"""
知识图谱管理器
使用 Neo4j 存储和查询对话知识图谱
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.documents import Document
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer

from config.settings import settings
from core.llm.llm_manager import get_llm_manager


class KnowledgeGraphManager:
    """知识图谱管理器"""

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        初始化知识图谱管理器

        Args:
            uri: Neo4j URI
            username: 用户名
            password: 密码
        """
        self.uri = uri or settings.NEO4J_URI
        self.username = username or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD

        # 验证配置
        if not self.uri or not self.password:
            raise ValueError("Neo4j URI 和密码必须配置")

        # 初始化 Neo4j 图数据库
        self.graph = Neo4jGraph(
            url=self.uri,
            username=self.username,
            password=self.password
        )

        # 初始化 LLM 图转换器
        self.llm_manager = get_llm_manager()
        self.graph_transformer = LLMGraphTransformer(
            llm=self.llm_manager.llm,
            allowed_nodes=settings.ALLOWED_NODES,
            allowed_relationships=settings.ALLOWED_RELATIONSHIPS
        )

        # 创建约束和索引
        self._create_constraints()

        print(f"✅ 知识图谱管理器初始化成功: {self.uri}")

    def _create_constraints(self):
        """创建图数据库约束和索引"""
        try:
            # 创建唯一性约束
            constraints = [
                "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
                "CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE"
            ]

            for constraint in constraints:
                try:
                    self.graph.query(constraint)
                except Exception as e:
                    # 约束可能已存在
                    pass

            print("✅ 图数据库约束创建成功")
        except Exception as e:
            print(f"警告: 创建约束失败: {e}")

    def extract_and_store(
        self,
        dialogue: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从对话中抽取实体和关系，并存储到知识图谱

        Args:
            dialogue: 对话文本
            session_id: 会话 ID
            metadata: 额外的元数据

        Returns:
            抽取结果统计
        """
        try:
            # 创建文档
            doc_metadata = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            if metadata:
                doc_metadata.update(metadata)

            document = Document(page_content=dialogue, metadata=doc_metadata)

            # 使用 LLM 抽取图结构
            graph_documents = self.graph_transformer.convert_to_graph_documents(
                [document]
            )

            # 添加会话节点
            self._ensure_session_node(session_id)

            # 添加到 Neo4j
            self.graph.add_graph_documents(graph_documents)

            # 为新创建的节点添加 session_id 标签（用于查询）
            for gd in graph_documents:
                for node in gd.nodes:
                    try:
                        # 使用节点的 id 来更新
                        cypher = """
                        MATCH (n)
                        WHERE n.id = $node_id
                        SET n.session_id = $session_id
                        RETURN n
                        """
                        self.graph.query(cypher, params={
                            "node_id": node.id,
                            "session_id": session_id
                        })
                    except:
                        pass

            # 统计结果
            stats = {
                "nodes_created": sum(len(gd.nodes) for gd in graph_documents),
                "relationships_created": sum(len(gd.relationships) for gd in graph_documents)
            }

            print(f"✅ 成功抽取并存储: {stats['nodes_created']} 个节点, {stats['relationships_created']} 个关系")

            return stats

        except Exception as e:
            print(f"❌ 抽取和存储失败: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _ensure_session_node(self, session_id: str):
        """确保会话节点存在"""
        query = """
        MERGE (s:Session {id: $session_id})
        SET s.created_at = COALESCE(s.created_at, datetime())
        RETURN s
        """
        self.graph.query(query, params={"session_id": session_id})

    def query_relevant_subgraph(
        self,
        query_text: str,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        查询相关的子图

        Args:
            query_text: 查询文本
            session_id: 会话 ID（如果指定，限制在该会话内）
            limit: 返回结果数量限制

        Returns:
            相关节点和关系列表
        """
        try:
            # 构建查询：查找与查询文本相关的节点和关系
            if session_id:
                cypher = """
                MATCH (s:Session {id: $session_id})-[:HAS_CONVERSATION]->(conv)
                MATCH (conv)-[r]->(n)
                WHERE n.name CONTAINS $query_text OR n.description CONTAINS $query_text
                RETURN n, r
                LIMIT $limit
                """
                params = {"session_id": session_id, "query_text": query_text, "limit": limit}
            else:
                cypher = """
                MATCH (n)-[r]-(m)
                WHERE n.name CONTAINS $query_text OR n.description CONTAINS $query_text
                   OR m.name CONTAINS $query_text OR m.description CONTAINS $query_text
                RETURN n, r, m
                LIMIT $limit
                """
                params = {"query_text": query_text, "limit": limit}

            results = self.graph.query(cypher, params=params)
            return results

        except Exception as e:
            print(f"❌ 查询子图失败: {e}")
            return []

    def get_user_preferences(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取用户偏好

        Args:
            session_id: 会话 ID
            limit: 返回数量

        Returns:
            偏好列表
        """
        try:
            # 查询用户相关的 LIKES 关系
            cypher = """
            MATCH (u:User {session_id: $session_id})-[r:LIKES]->(p:Preference)
            RETURN u.name AS user, p.name AS preference, p.description AS description
            LIMIT $limit
            """
            results = self.graph.query(cypher, params={"session_id": session_id, "limit": limit})
            return results

        except Exception as e:
            print(f"❌ 获取用户偏好失败: {e}")
            return []

    def get_conversation_summary(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        获取对话摘要统计

        Args:
            session_id: 会话 ID

        Returns:
            对话统计信息
        """
        try:
            # 统计节点和关系数量
            cypher = """
            MATCH (n)
            WHERE n.session_id = $session_id
            WITH labels(n)[0] AS node_type, count(*) AS count
            RETURN node_type, count
            """
            node_stats = self.graph.query(cypher, params={"session_id": session_id})

            cypher = """
            MATCH ()-[r]->()
            WHERE r.session_id = $session_id
            WITH type(r) AS rel_type, count(*) AS count
            RETURN rel_type, count
            """
            rel_stats = self.graph.query(cypher, params={"session_id": session_id})

            return {
                "nodes": node_stats,
                "relationships": rel_stats
            }

        except Exception as e:
            print(f"❌ 获取对话摘要失败: {e}")
            return {"error": str(e)}

    def get_graph_data(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取用于可视化的图数据

        Args:
            session_id: 会话 ID（可选）

        Returns:
            图数据（节点和边）
        """
        try:
            # 获取节点：使用 n.id 作为标识符
            if session_id:
                cypher = """
                MATCH (n)
                WHERE n.session_id = $session_id
                RETURN DISTINCT n.id AS id, labels(n)[0] AS type
                LIMIT 100
                """
                nodes_result = self.graph.query(cypher, params={"session_id": session_id})

                # 获取关系
                cypher = """
                MATCH (n)-[r]->(m)
                WHERE n.session_id = $session_id OR m.session_id = $session_id
                RETURN n.id AS source, m.id AS target, type(r) AS rel_type
                LIMIT 100
                """
                edges_result = self.graph.query(cypher, params={"session_id": session_id})
            else:
                cypher = """
                MATCH (n)
                RETURN DISTINCT n.id AS id, labels(n)[0] AS type
                LIMIT 100
                """
                nodes_result = self.graph.query(cypher)

                cypher = """
                MATCH (n)-[r]->(m)
                RETURN n.id AS source, m.id AS target, type(r) AS rel_type
                LIMIT 100
                """
                edges_result = self.graph.query(cypher)

            # 转换为可视化格式
            nodes = []
            edges = []
            node_ids_set = set()

            # 处理节点
            for record in nodes_result:
                node_id = record.get("id", "Unknown")
                node_type = record.get("type", "Unknown")

                nodes.append({
                    "id": node_id,
                    "label": node_id,
                    "group": node_type,
                    "title": f"类型: {node_type}\n名称: {node_id}"
                })
                node_ids_set.add(node_id)

            # 处理边
            for record in edges_result:
                source = record.get("source", "")
                target = record.get("target", "")
                rel_type = record.get("rel_type", "RELATED_TO")

                if source and target and source in node_ids_set and target in node_ids_set:
                    edges.append({
                        "from": source,
                        "to": target,
                        "label": rel_type,
                        "title": rel_type
                    })

            print(f"  ✅ 获取图数据成功: {len(nodes)} 节点, {len(edges)} 边")

            return {
                "nodes": nodes,
                "edges": edges
            }

        except Exception as e:
            print(f"❌ 获取图数据失败: {e}")
            import traceback
            traceback.print_exc()
            return {"nodes": [], "edges": []}

    def clear_session(self, session_id: str) -> None:
        """
        清除会话的所有数据

        Args:
            session_id: 会话 ID
        """
        try:
            cypher = """
            MATCH (n)
            WHERE n.session_id = $session_id
            DETACH DELETE n
            """
            self.graph.query(cypher, params={"session_id": session_id})
            print(f"✅ 会话 {session_id} 的数据已清除")

        except Exception as e:
            print(f"❌ 清除会话失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取图数据库统计信息

        Returns:
            统计信息
        """
        try:
            # 获取节点总数
            node_count = self.graph.query("MATCH (n) RETURN count(n) AS count")[0]["count"]

            # 获取关系总数
            rel_count = self.graph.query("MATCH ()-[r]->() RETURN count(r) AS count")[0]["count"]

            return {
                "total_nodes": node_count,
                "total_relationships": rel_count,
                "uri": self.uri
            }

        except Exception as e:
            return {"error": str(e)}


# 全局知识图谱管理器实例
_kg_manager: Optional[KnowledgeGraphManager] = None


def get_kg_manager() -> KnowledgeGraphManager:
    """获取全局知识图谱管理器实例"""
    global _kg_manager
    if _kg_manager is None:
        _kg_manager = KnowledgeGraphManager()
    return _kg_manager


if __name__ == "__main__":
    # 测试知识图谱管理器
    print("=== 知识图谱管理器测试 ===\n")

    try:
        # 初始化
        kg_manager = KnowledgeGraphManager()
        print()

        # 测试抽取和存储
        print("测试 1: 从对话抽取实体和关系")
        dialogue = """
        用户: 我喜欢听摇滚音乐，特别是重金属。
        偶像: 真的吗？我也很喜欢重金属！你最喜欢哪个乐队？
        用户: 我最喜欢 Metallica。
        偶像: Metallica 超棒的！他们的 Enter Sandland 是经典。
        """

        stats = kg_manager.extract_and_store(
            dialogue=dialogue,
            session_id="test_session"
        )
        print(f"抽取结果: {stats}\n")

        # 测试查询
        print("测试 2: 查询相关子图")
        results = kg_manager.query_relevant_subgraph(
            query_text="音乐",
            session_id="test_session"
        )
        print(f"找到 {len(results)} 条相关记录\n")

        # 测试获取统计
        print("测试 3: 获取统计信息")
        stats = kg_manager.get_stats()
        print(f"统计信息: {stats}\n")

        # 测试获取图数据
        print("测试 4: 获取可视化数据")
        graph_data = kg_manager.get_graph_data(session_id="test_session")
        print(f"节点数: {len(graph_data['nodes'])}")
        print(f"边数: {len(graph_data['edges'])}\n")

        print("✅ 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
