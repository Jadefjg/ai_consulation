"""RAG检索增强服务"""
import json
import os
import sys
import time
from typing import AsyncGenerator, List, Dict, Any
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from core.config import settings
from rag.loader import load_document
from rag.splitter import split_text
from rag.vector_store import get_vector_store
from models.knowledge import KnowledgeFile, KnowledgeChunk
from services.graph_service import get_graph_service


def _safe_console_text(text: str) -> str:
    """将文本转为当前控制台可安全输出的字符串，避免GBK编码报错"""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def _rag_log(tag: str, message: str) -> None:
    """RAG流程控制台日志（兼容Windows GBK控制台，日志失败不影响业务）"""
    try:
        print(f"[RAG-{tag}] {_safe_console_text(message)}", flush=True)
    except Exception:
        pass


class RagService:
    """RAG检索增强生成服务"""

    def __init__(self):
        llm_kwargs = {
            "model": settings.llm_model,
            "openai_api_key": settings.openai_api_key,
            "openai_api_base": settings.openai_base_url,
            "streaming": True,
            "temperature": settings.llm_temperature,
            "timeout": 300,
            "max_retries": 1,
        }
        if not settings.llm_reasoning and any(
            token in (settings.openai_base_url or "").lower()
            for token in ("11434", "ollama", "localhost", "127.0.0.1", "host.docker.internal")
        ):
            llm_kwargs["extra_body"] = {"think": False}
        self.llm = ChatOpenAI(**llm_kwargs)
        self.vector_store = get_vector_store()
        self.graph_service = get_graph_service()

    def process_file(self, db: Session, file_record: KnowledgeFile) -> int:
        """
        处理知识库文件：解析、分块、向量化
        :return: 分块数量
        """
        file_record.vector_status = 1
        db.commit()
        try:
            # 解析文件 - 支持绝对路径和uploads33相对路径
            file_path = file_record.file_path.replace("\\", "/")
            if os.path.isabs(file_path) or (len(file_path) > 1 and file_path[1] == ":"):
                abs_path = file_path
            elif file_path.startswith("/uploads33/"):
                abs_path = os.path.join(settings.upload_dir, file_path.replace("/uploads33/", ""))
            else:
                abs_path = os.path.join(settings.upload_dir, file_path)
            abs_path = abs_path.replace("/", os.sep)
            text = load_document(abs_path)
            chunks = split_text(text)
            # 清除旧分块
            db.query(KnowledgeChunk).filter(KnowledgeChunk.file_id == file_record.id).delete()
            self.vector_store.delete_by_file_id(file_record.id)
            # 写入新分块
            texts, metadatas, ids = [], [], []
            for idx, chunk in enumerate(chunks):
                vector_id = f"file_{file_record.id}_chunk_{idx}"
                db_chunk = KnowledgeChunk(
                    file_id=file_record.id,
                    chunk_index=idx,
                    content=chunk,
                    vector_id=vector_id,
                )
                db.add(db_chunk)
                texts.append(chunk)
                metadatas.append({
                    "file_id": str(file_record.id),
                    "file_name": file_record.file_name,
                    "chunk_index": idx,
                })
                ids.append(vector_id)
            db.commit()
            if texts:
                self.vector_store.add_documents(texts, metadatas, ids)
            file_record.chunk_count = len(chunks)
            file_record.vector_status = 2
            db.commit()
            return len(chunks)
        except Exception as e:
            file_record.vector_status = 3
            db.commit()
            _rag_log("向量化", f"文件处理失败 id={file_record.id} name={file_record.file_name}: {e}")
            raise e

    def _extract_symptoms(self, query: str) -> List[str]:
        """从查询中提取症状关键词，并做别名归一化"""
        aliases = self.graph_service.SYMPTOM_ALIASES
        common_symptoms = [
            "头痛", "发热", "咳嗽", "乏力", "恶心", "呕吐", "腹泻", "腹痛",
            "胸闷", "心悸", "头晕", "失眠", "皮疹", "瘙痒", "水肿", "出血",
            "关节痛", "腰痛", "视力模糊", "耳鸣", "鼻塞", "咽痛", "流涕",
            "胸痛", "感冒", "过敏", "便秘", "尿频",
        ]
        # 别名也参与匹配
        candidates = list(dict.fromkeys([*aliases.keys(), *common_symptoms]))
        found = []
        for s in candidates:
            if s in query:
                found.append(aliases.get(s, s))
        return list(dict.fromkeys(found))

    def _build_context(self, query: str) -> tuple[str, List[Dict], List[Dict]]:
        """
        构建RAG上下文
        :return: (context_text, references, graph_results)
        """
        _rag_log("检索", f"开始构建上下文，用户问题: {query}")

        # 向量检索
        vector_start = time.time()
        vector_results = self.vector_store.search(query)
        vector_cost = int((time.time() - vector_start) * 1000)
        _rag_log("检索", f"向量检索完成，耗时 {vector_cost}ms，命中 {len(vector_results)} 条")
        references = []
        context_parts = []
        for i, item in enumerate(vector_results):
            meta = item.get("metadata", {})
            distance = item.get("distance", 0)
            file_name = meta.get("file_name", "未知")
            content_preview = item["content"][:80].replace("\n", " ")
            _rag_log(
                "检索",
                f"  文档{i + 1}: 文件={file_name}, 相似度距离={distance:.4f}, 摘要={content_preview}...",
            )
            ref = {
                "index": i + 1,
                "file_name": file_name,
                "content": item["content"][:200],
            }
            references.append(ref)
            context_parts.append(f"[文档{i+1}] {item['content']}")

        # 图谱推理
        symptoms = self._extract_symptoms(query)
        graph_results = []
        if symptoms:
            _rag_log("图谱", f"提取症状关键词: {symptoms}")
            graph_start = time.time()
            diseases = self.graph_service.infer_diseases_by_symptoms(symptoms)
            graph_cost = int((time.time() - graph_start) * 1000)
            graph_results = diseases
            _rag_log("图谱", f"知识图谱检索完成，耗时 {graph_cost}ms，命中 {len(diseases)} 条")
            for idx, d in enumerate(diseases[:5], start=1):
                _rag_log(
                    "图谱",
                    f"  结果{idx}: 疾病={d.get('disease')}, 匹配症状数={d.get('match_count')}, "
                    f"科室={d.get('department', '未知')}, 匹配项={d.get('matched', [])}",
                )
            if diseases:
                graph_text = "知识图谱推理结果：\n"
                for d in diseases[:5]:
                    graph_text += f"- 可能疾病: {d.get('disease')} (匹配症状数:{d.get('match_count')}), 建议科室: {d.get('department', '未知')}\n"
                context_parts.append(graph_text)
        else:
            _rag_log("图谱", "未匹配到症状关键词，跳过知识图谱检索")

        context = "\n\n".join(context_parts) if context_parts else "暂无相关知识库内容。"
        _rag_log("检索", f"上下文构建完成，参考内容长度 {len(context)} 字符")
        return context, references, graph_results

    async def chat_stream(self, query: str, history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """
        SSE流式对话
        :yield: SSE格式数据
        """
        start_time = time.time()
        history = history or []
        _rag_log("LLM", f"收到问诊请求，历史消息 {len(history)} 条")
        context, references, graph_results = self._build_context(query)

        system_prompt = """你是AI智能医疗问诊助手，基于提供的知识库和医疗知识图谱为用户提供健康咨询。
请注意：
1. 你的回答仅供参考，不能替代专业医生的诊断
2. 如有严重症状，请建议用户及时就医
3. 结合知识库内容和图谱推理结果给出专业、易懂的建议
4. 回答要条理清晰，适当分点说明"""

        user_prompt = f"""参考知识：
{context}

用户问题：{query}

请基于以上参考信息回答用户问题。"""

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-6:]:
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_prompt})

        _rag_log(
            "LLM",
            f"请求大模型: model={settings.llm_model}, base_url={settings.openai_base_url}, "
            f"消息数={len(messages)}, 用户问题长度={len(query)}, 参考上下文长度={len(context)}",
        )
        for idx, msg in enumerate(messages):
            preview = msg["content"][:100].replace("\n", " ")
            _rag_log("LLM", f"  消息{idx + 1} [{msg['role']}]: {preview}...")

        llm_start = time.time()
        full_content = ""
        chunk_count = 0
        try:
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_content += chunk.content
                    chunk_count += 1
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.content}, ensure_ascii=False)}\n\n"
        except Exception as e:
            llm_cost = int((time.time() - llm_start) * 1000)
            _rag_log("LLM", f"大模型请求失败，耗时 {llm_cost}ms，错误: {e}")
            raise

        llm_cost = int((time.time() - llm_start) * 1000)
        total_cost = int((time.time() - start_time) * 1000)
        _rag_log(
            "LLM",
            f"大模型回复完成，流式块数={chunk_count}，回复长度={len(full_content)} 字符，"
            f"LLM耗时={llm_cost}ms，总耗时={total_cost}ms",
        )
        reply_preview = full_content[:150].replace("\n", " ")
        _rag_log("LLM", f"  回复摘要: {reply_preview}...")

        cost_time = int((time.time() - start_time) * 1000)
        yield f"data: {json.dumps({'type': 'done', 'references': references, 'graph': graph_results, 'cost_time': cost_time}, ensure_ascii=False)}\n\n"


_rag_service = None


def get_rag_service() -> RagService:
    """获取RAG服务单例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service
