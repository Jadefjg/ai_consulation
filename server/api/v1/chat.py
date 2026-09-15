"""AI问诊接口 - SSE流式"""
import json
import logging
import re
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.config import settings
from core.response import success, page_result
from db.session import get_db
from models.consult import ConsultSession, ConsultMessage
from models.clinical import AIConsultReview, AIResponseEvaluation
from models.user import User
from schemas.common import ChatRequest
from services.rag_service import get_rag_service
from services.safety_service import DISCLAIMER, assess_text, review_output, safety_event
from services.evaluation_service import evaluate_answer
from utils.helpers import format_datetime

router = APIRouter()
logger = logging.getLogger(__name__)

EMERGENCY_PATTERNS = (
    r"胸痛|胸口(?:剧烈)?疼痛|心前区疼痛",
    r"呼吸困难|喘不上气|无法呼吸|窒息",
    r"意识不清|失去意识|昏迷|晕厥",
    r"口角歪斜|一侧肢体无力|言语不清",
    r"大出血|血流不止|呕血|咯血",
    r"严重过敏|喉头水肿|全身抽搐",
    r"自杀|自残|不想活",
)
EMERGENCY_NOTICE = (
    "**紧急就医提示：** 你的描述可能涉及急症风险。请立即拨打 120 或前往最近的急诊，"
    "不要等待线上回复，也不要独自驾车。以下信息仅作辅助，不能替代急救处置。\n\n"
)


def _needs_emergency_notice(message: str) -> bool:
    """以保守的关键词规则识别需优先线下急救的描述。"""
    normalized = re.sub(r"\s+", "", message or "")
    return any(re.search(pattern, normalized) for pattern in EMERGENCY_PATTERNS)


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """获取用户会话列表"""
    items = db.query(ConsultSession).filter(ConsultSession.user_id == current.user_id).order_by(ConsultSession.update_time.desc()).all()
    review_map = {
        r.session_id: r for r in db.query(AIConsultReview).filter(
            AIConsultReview.session_id.in_([s.id for s in items])
        ).all()
    } if items else {}
    data = []
    for s in items:
        review = review_map.get(s.id)
        data.append({
            "id": s.id, "title": s.title, "message_count": s.message_count,
            "create_time": format_datetime(s.create_time),
            "human_review": {
                "id": review.id,
                "status": review.review_status,
                "status_text": {0: "待医生审核", 1: "已审核通过", 2: "医生已修订"}.get(review.review_status, "未知"),
            } if review else None,
        })
    return success(data)


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """获取会话消息（仅本人会话）"""
    session = db.query(ConsultSession).filter(
        ConsultSession.id == session_id,
        ConsultSession.user_id == current.user_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = db.query(ConsultMessage).filter(ConsultMessage.session_id == session_id).order_by(ConsultMessage.id).all()
    evaluations = {
        item.message_id: item
        for item in db.query(AIResponseEvaluation).filter(
            AIResponseEvaluation.message_id.in_([m.id for m in msgs])
        ).all()
    } if msgs else {}
    data = []
    for m in msgs:
        evaluation = evaluations.get(m.id)
        safety = None
        if evaluation:
            reasons = []
            try:
                reasons = json.loads(evaluation.details_json or "{}").get("reasons", [])
            except (TypeError, ValueError):
                reasons = []
            safety = {
                "level": evaluation.safety_level,
                "action": evaluation.safety_action,
                "reasons": reasons,
                "requires_human_review": evaluation.safety_action != "allow",
                "groundedness": evaluation.groundedness,
                "citation_coverage": evaluation.citation_coverage,
            }
        data.append({
            "id": m.id, "role": m.role, "content": m.content,
            "references_json": m.references_json, "graph_json": m.graph_json,
            "delivery_status": m.delivery_status, "error_message": m.error_message,
            "safety": safety, "create_time": format_datetime(m.create_time),
        })
    return success(data)


@router.post("/send")
async def chat_send(req: ChatRequest, request: Request, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """AI问诊 - SSE流式回复"""
    if req.session_id:
        session = db.query(ConsultSession).filter(
            ConsultSession.id == req.session_id,
            ConsultSession.user_id == current.user_id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或无权访问")
    else:
        title = req.message[:20] + ("..." if len(req.message) > 20 else "")
        session = ConsultSession(user_id=current.user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)

    user_msg = ConsultMessage(session_id=session.id, role="user", content=req.message, delivery_status="completed")
    assistant_msg = ConsultMessage(session_id=session.id, role="assistant", content="", delivery_status="pending")
    db.add_all([user_msg, assistant_msg])
    session.message_count = (session.message_count or 0) + 2
    db.commit()
    db.refresh(assistant_msg)

    history_msgs = db.query(ConsultMessage).filter(ConsultMessage.session_id == session.id).order_by(ConsultMessage.id).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs[:-2]]

    session_id = session.id
    assistant_message_id = assistant_msg.id

    async def event_generator():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        full_content = ""
        references = []
        graph_results = []
        cost_time = 0
        delivery_status = "completed"
        error_message = None
        stream = None
        next_task = None
        deadline = time.monotonic() + settings.sse_max_seconds
        try:
            safety = assess_text(req.message)
            if safety.action == "escalate":
                full_content += f"{DISCLAIMER}\n\n"
                yield f"data: {json.dumps({'type': 'safety', **safety_event(safety)}, ensure_ascii=False)}\n\n"
            if _needs_emergency_notice(req.message):
                full_content += EMERGENCY_NOTICE
                yield f"data: {json.dumps({'type': 'content', 'content': EMERGENCY_NOTICE, 'safety_level': 'emergency'}, ensure_ascii=False)}\n\n"
            stream = get_rag_service().chat_stream(req.message, history, db)
            while True:
                if await request.is_disconnected():
                    raise asyncio.CancelledError("client disconnected")
                if time.monotonic() >= deadline:
                    raise TimeoutError("SSE generation exceeded time limit")
                if next_task is None:
                    next_task = asyncio.create_task(anext(stream))
                done, _ = await asyncio.wait({next_task}, timeout=settings.sse_heartbeat_seconds)
                if not done:
                    yield ": heartbeat\n\n"
                    continue
                try:
                    chunk = next_task.result()
                except StopAsyncIteration:
                    next_task = None
                    break
                next_task = None
                if chunk.startswith("data: "):
                    try:
                        data = json.loads(chunk[6:].strip())
                        if data.get("type") == "content":
                            full_content += data["content"]
                        elif data.get("type") == "done":
                            references = data.get("references", [])
                            graph_results = data.get("graph", [])
                            cost_time = data.get("cost_time", 0)
                            if DISCLAIMER not in full_content:
                                disclaimer_content = "\n\n" + DISCLAIMER
                                full_content += disclaimer_content
                                yield f"data: {json.dumps({'type': 'content', 'content': disclaimer_content}, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError:
                        logger.warning(
                            "ignored malformed SSE payload",
                            extra={"event": "malformed_sse", "session_id": session_id},
                        )
                yield chunk
        except asyncio.CancelledError:
            delivery_status = "cancelled"
            error_message = "客户端断开连接或请求被取消"
            logger.info("AI consultation cancelled", extra={"event": "sse_cancelled", "session_id": session_id})
            raise
        except Exception:
            delivery_status = "failed"
            error_message = "AI 回复生成失败或超时"
            logger.exception("AI consultation failed: session_id=%s", session_id)
            failure_text = "抱歉，本次 AI 回复未能完成。请稍后重试；如症状严重或持续加重，请及时线下就医。"
            full_content = f"{full_content}{failure_text}"
            yield f"data: {json.dumps({'type': 'error', 'message': failure_text}, ensure_ascii=False)}\n\n"
        finally:
            if next_task and not next_task.done():
                next_task.cancel()
            if stream is not None:
                try:
                    await stream.aclose()
                except RuntimeError:
                    logger.debug("SSE upstream stream already closed", extra={"event": "sse_stream_closed", "session_id": session_id})
            if delivery_status == "completed" and DISCLAIMER not in full_content:
                full_content = f"{full_content}\n\n{DISCLAIMER}"
            output_safety = review_output(req.message, full_content)
            if output_safety.action != "allow":
                if DISCLAIMER not in full_content:
                    disclaimer_content = f"\n\n{DISCLAIMER}"
                    full_content += disclaimer_content
            evaluation = evaluate_answer(full_content, references, DISCLAIMER)
            # 将最终审核结果作为独立 SSE 事件发送给前端，避免客户端只能看到文本而
            # 无法区分普通健康建议、需医生复核和急症升级。
            if delivery_status != "cancelled":
                yield f"data: {json.dumps({'type': 'safety', **safety_event(output_safety), 'groundedness': evaluation.groundedness, 'citation_coverage': evaluation.citation_coverage}, ensure_ascii=False)}\n\n"
            logger.info(
                "AI answer evaluated: safety=%s metrics=%s",
                output_safety.level,
                evaluation.as_dict(),
                extra={"event": "ai_answer_evaluated", "session_id": session_id},
            )
            from db.session import SessionLocal
            sdb = SessionLocal()
            try:
                saved = sdb.query(ConsultMessage).filter(ConsultMessage.id == assistant_message_id).first()
                if saved:
                    saved.content = full_content
                    saved.references_json = json.dumps(references, ensure_ascii=False)
                    saved.graph_json = json.dumps(graph_results, ensure_ascii=False)
                    saved.cost_time = cost_time
                    saved.delivery_status = delivery_status
                    saved.error_message = error_message
                    sdb.merge(AIResponseEvaluation(
                        message_id=saved.id,
                        safety_level=output_safety.level,
                        safety_action=output_safety.action,
                        citation_coverage=str(evaluation.citation_coverage),
                        groundedness=str(evaluation.groundedness),
                        disclaimer_present=1 if evaluation.safety_disclaimer else 0,
                        details_json=json.dumps({"reasons": output_safety.reasons, **evaluation.as_dict()}, ensure_ascii=False),
                    ))
                    sdb.commit()
            except Exception:
                sdb.rollback()
                logger.exception("Failed to persist AI response state: session_id=%s", session_id)
            finally:
                sdb.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


@router.get("/admin/sessions")
def admin_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员查看所有问诊记录"""
    q = db.query(ConsultSession)
    total = q.count()
    items = q.order_by(ConsultSession.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    user_ids = {s.user_id for s in items}
    user_map = {
        u.id: u.real_name or u.username
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}
    data = [{
        "id": s.id, "user_id": s.user_id, "user_name": user_map.get(s.user_id, ""),
        "title": s.title, "message_count": s.message_count,
        "create_time": format_datetime(s.create_time),
    } for s in items]
    return page_result(data, total, page, page_size)
