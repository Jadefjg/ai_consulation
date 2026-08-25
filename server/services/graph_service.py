"""Neo4j知识图谱服务"""
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from core.config import settings


class GraphService:
    """医疗知识图谱服务"""

    # 常见症状别名映射到图谱标准名称
    SYMPTOM_ALIASES = {
        "头疼": "头痛",
        "头胀": "头痛",
        "头昏": "头晕",
        "发烧": "发热",
        "发高烧": "发热",
        "高烧": "发热",
        "低烧": "发热",
        "肚子痛": "腹痛",
        "胃疼": "腹痛",
        "胸口痛": "胸痛",
        "胸口闷": "胸闷",
        "没力气": "乏力",
        "疲倦": "乏力",
        "疲劳": "乏力",
        "想吐": "恶心",
        "拉肚子": "腹泻",
        "关节疼": "关节痛",
        "腰疼": "腰痛",
        "看不清": "视力模糊",
        "流鼻涕": "流涕",
        "喉咙痛": "咽痛",
        "嗓子痛": "咽痛",
    }

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self):
        """关闭连接"""
        self.driver.close()

    def _normalize_symptoms(self, symptoms: List[str]) -> List[str]:
        """将用户输入的症状别名转换为图谱标准名称"""
        normalized: List[str] = []
        for symptom in symptoms:
            name = (symptom or "").strip()
            if not name:
                continue
            normalized.append(self.SYMPTOM_ALIASES.get(name, name))
        # 去重并保持顺序
        return list(dict.fromkeys(normalized))

    def infer_diseases_by_symptoms(self, symptoms: List[str]) -> List[Dict]:
        """
        根据症状推理可能疾病（共现计数排序）
        :param symptoms: 症状列表
        :return: 疾病列表 [{name, disease, match_count, probability, department, matched}]
        """
        normalized_symptoms = self._normalize_symptoms(symptoms)
        if not normalized_symptoms:
            return []
        query = """
        UNWIND $symptoms AS symptom_name
        MATCH (s:Symptom {name: symptom_name})<-[:HAS_SYMPTOM]-(d:Disease)
        OPTIONAL MATCH (d)-[:BELONGS_TO]->(dep:Department)
        WITH d, dep, count(s) AS match_count, collect(symptom_name) AS matched
        ORDER BY match_count DESC
        LIMIT 10
        RETURN d.name AS disease, match_count, dep.name AS department, matched
        """
        total = len(normalized_symptoms)
        with self.driver.session() as session:
            result = session.run(query, symptoms=normalized_symptoms)
            rows = [dict(r) for r in result]
        return [
            {
                "name": row["disease"],
                "disease": row["disease"],
                "match_count": row["match_count"],
                "probability": round(row["match_count"] / total, 2),
                "department": row.get("department") or "-",
                "matched": row.get("matched") or [],
            }
            for row in rows
        ]

    def get_disease_detail(self, disease_name: str) -> Dict[str, Any]:
        """
        获取疾病详情子图
        :param disease_name: 疾病名称
        """
        query = """
        MATCH (d:Disease {name: $name})
        OPTIONAL MATCH (d)-[:HAS_SYMPTOM]->(s:Symptom)
        OPTIONAL MATCH (d)-[:BELONGS_TO]->(dep:Department)
        OPTIONAL MATCH (d)-[:RECOMMEND_DRUG]->(drug:Drug)
        OPTIONAL MATCH (d)-[:NEED_CHECK]->(chk:Check)
        OPTIONAL MATCH (d)-[:ACCOMPANY_WITH]->(comp:Disease)
        OPTIONAL MATCH (d)-[:SHOULD_EAT]->(food:Food)
        OPTIONAL MATCH (d)-[:AVOID_EAT]->(avoid:Food)
        RETURN d.name AS disease,
               collect(DISTINCT s.name) AS symptoms,
               dep.name AS department,
               collect(DISTINCT drug.name) AS drugs,
               collect(DISTINCT chk.name) AS checks,
               collect(DISTINCT comp.name) AS complications,
               collect(DISTINCT food.name) AS should_eat,
               collect(DISTINCT avoid.name) AS avoid_eat
        """
        with self.driver.session() as session:
            record = session.run(query, name=disease_name).single()
            if not record:
                return {}
            detail = dict(record)
            drugs = detail.get("drugs") or []
            checks = detail.get("checks") or []
            detail["name"] = detail.get("disease") or disease_name
            detail["description"] = detail.get("description") or (
                f"建议检查：{'、'.join(checks)}" if checks else "-"
            )
            detail["treatment"] = detail.get("treatment") or (
                f"常用药物：{'、'.join(drugs)}" if drugs else "-"
            )
            return detail

    def get_entity_subgraph(self, entity_name: str, depth: int = 1) -> Dict[str, Any]:
        """
        获取实体邻居子图（供前端可视化）
        :return: {nodes: [{id, label, category}], links: [{source, target, relation}]}
        """
        query = """
        MATCH (n) WHERE n.name = $name
        CALL {
            WITH n
            MATCH path = (n)-[r*1..2]-(m)
            RETURN n, r, m
            LIMIT 50
        }
        RETURN n, r, m
        """
        nodes_map = {}
        links = []
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n {name: $name})-[r]-(m) RETURN n, type(r) AS rel, m LIMIT 30",
                name=entity_name,
            )
            for record in result:
                n = record["n"]
                m = record["m"]
                rel = record["rel"]
                n_id = n.element_id
                m_id = m.element_id
                n_label = list(n.labels)[0] if n.labels else "Unknown"
                m_label = list(m.labels)[0] if m.labels else "Unknown"
                nodes_map[n_id] = {"id": n_id, "name": n.get("name", ""), "category": n_label}
                nodes_map[m_id] = {"id": m_id, "name": m.get("name", ""), "category": m_label}
                links.append({"source": n_id, "target": m_id, "relation": rel})
        return {"nodes": list(nodes_map.values()), "links": links}

    def search_entities(self, keyword: str) -> List[Dict]:
        """搜索图谱实体"""
        query = """
        MATCH (n) WHERE n.name CONTAINS $keyword
        RETURN n.name AS name, labels(n)[0] AS label
        LIMIT 20
        """
        with self.driver.session() as session:
            result = session.run(query, keyword=keyword)
            return [dict(r) for r in result]

    def get_full_graph(self) -> Dict[str, Any]:
        """
        获取完整知识图谱（默认可视化展示全部节点与关系）
        :return: {nodes: [{id, name, category}], links: [{source, target, relation}]}
        """
        nodes_map: Dict[str, Dict] = {}
        links: List[Dict] = []
        query = """
        MATCH (a)-[r]->(b)
        RETURN a, type(r) AS rel, b
        """
        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                a = record["a"]
                b = record["b"]
                rel = record["rel"]
                a_id = a.element_id
                b_id = b.element_id
                a_label = list(a.labels)[0] if a.labels else "Unknown"
                b_label = list(b.labels)[0] if b.labels else "Unknown"
                nodes_map[a_id] = {"id": a_id, "name": a.get("name", ""), "category": a_label}
                nodes_map[b_id] = {"id": b_id, "name": b.get("name", ""), "category": b_label}
                links.append({"source": a_id, "target": b_id, "relation": rel})
        return {"nodes": list(nodes_map.values()), "links": links}

    def get_graph_stats(self) -> Dict[str, int]:
        """获取图谱统计"""
        query = """
        MATCH (n) WITH labels(n)[0] AS label, count(n) AS cnt
        RETURN label, cnt ORDER BY cnt DESC
        """
        with self.driver.session() as session:
            result = session.run(query)
            return {r["label"]: r["cnt"] for r in result}


_graph_service: Optional[GraphService] = None


def get_graph_service() -> GraphService:
    """获取图谱服务单例"""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service
