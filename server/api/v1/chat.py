"""AI问诊接口 - SSE流式"""
import json
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.response import success, page_result
from db.session import get_db
from models.consult import ConsultSession, ConsultMessage
from models.user import User
from schemas.common import ChatRequest
from services.rag_service import get_rag_service
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
    data = [{"id": s.id, "title": s.title, "message_count": s.message_count, "create_time": format_datetime(s.create_time)} for s in items]
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
    data = [{
        "id": m.id, "role": m.role, "content": m.content,
        "references_json": m.references_json, "graph_json": m.graph_json,
        "create_time": format_datetime(m.create_time),
    } for m in msgs]
    return success(data)


@router.post("/send")
async def chat_send(req: ChatRequest, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
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

    user_msg = ConsultMessage(session_id=session.id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()

    history_msgs = db.query(ConsultMessage).filter(ConsultMessage.session_id == session.id).order_by(ConsultMessage.id).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs[:-1]]

    session_id = session.id

    async def event_generator():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        full_content = ""
        references = []
        graph_results = []
        cost_time = 0
        try:
            if _needs_emergency_notice(req.message):
                full_content += EMERGENCY_NOTICE
                yield f"data: {json.dumps({'type': 'content', 'content': EMERGENCY_NOTICE, 'safety_level': 'emergency'}, ensure_ascii=False)}\n\n"
            async for chunk in get_rag_service().chat_stream(req.message, history):
                yield chunk
                if chunk.startswith("data: "):
                    try:
                        data = json.loads(chunk[6:].strip())
                        if data.get("type") == "content":
                            full_content += data["content"]
                        elif data.get("type") == "done":
                            references = data.get("references", [])
                            graph_results = data.get("graph", [])
                            cost_time = data.get("cost_time", 0)
                    except json.JSONDecodeError:
                        pass
        except Exception:
            logger.exception("AI consultation failed: session_id=%s", session_id)
            failure_text = "抱歉，本次 AI 回复未能完成。请稍后重试；如症状严重或持续加重，请及时线下就医。"
            full_content = f"{full_content}{failure_text}"
            yield f"data: {json.dumps({'type': 'error', 'message': failure_text}, ensure_ascii=False)}\n\n"
        from db.session import SessionLocal
        sdb = SessionLocal()
        try:
            assistant_msg = ConsultMessage(
                session_id=session_id,
                role="assistant",
                content=full_content,
                references_json=json.dumps(references, ensure_ascii=False),
                graph_json=json.dumps(graph_results, ensure_ascii=False),
                cost_time=cost_time,
            )
            sdb.add(assistant_msg)
            sess = sdb.query(ConsultSession).filter(ConsultSession.id == session_id).first()
            if sess:
                sess.message_count = (sess.message_count or 0) + 2
            sdb.commit()
        except Exception:
            sdb.rollback()
            logger.exception("Failed to persist AI response: session_id=%s", session_id)
        finally:
            sdb.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
