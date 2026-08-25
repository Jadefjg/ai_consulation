"""AI问诊接口 - SSE流式"""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.response import success
from db.session import get_db
from models.consult import ConsultSession, ConsultMessage
from schemas.common import ChatRequest
from services.rag_service import get_rag_service
from utils.helpers import format_datetime

router = APIRouter()


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """获取用户会话列表"""
    items = db.query(ConsultSession).filter(ConsultSession.user_id == current.user_id).order_by(ConsultSession.update_time.desc()).all()
    data = [{"id": s.id, "title": s.title, "message_count": s.message_count, "create_time": format_datetime(s.create_time)} for s in items]
    return success(data)


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """获取会话消息"""
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
    # 获取或创建会话
    if req.session_id:
        session = db.query(ConsultSession).filter(ConsultSession.id == req.session_id, ConsultSession.user_id == current.user_id).first()
    else:
        session = None
    if not session:
        title = req.message[:20] + ("..." if len(req.message) > 20 else "")
        session = ConsultSession(user_id=current.user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)

    # 保存用户消息
    user_msg = ConsultMessage(session_id=session.id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()

    # 获取历史
    history_msgs = db.query(ConsultMessage).filter(ConsultMessage.session_id == session.id).order_by(ConsultMessage.id).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs[:-1]]

    session_id = session.id

    async def event_generator():
        # 先推送会话ID，便于前端关联新对话
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        full_content = ""
        references = []
        graph_results = []
        cost_time = 0
        try:
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
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
            return
        # 保存助手消息
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
        finally:
            sdb.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/admin/sessions")
def admin_sessions(
    page: int = 1, page_size: int = 10,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员查看所有问诊记录"""
    from core.response import page_result
    from models.user import User
    q = db.query(ConsultSession)
    total = q.count()
    items = q.order_by(ConsultSession.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    user_map = {u.id: u.real_name or u.username for u in db.query(User).all()}
    data = [{
        "id": s.id, "user_id": s.user_id, "user_name": user_map.get(s.user_id, ""),
        "title": s.title, "message_count": s.message_count,
        "create_time": format_datetime(s.create_time),
    } for s in items]
    return page_result(data, total, page, page_size)
