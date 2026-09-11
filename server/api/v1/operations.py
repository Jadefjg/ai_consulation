from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.deps import require_roles, CurrentUser
from core.response import success, page_result
from db.session import get_db
from models.operations import Notification, AuditLog

router = APIRouter()

@router.get("/notifications")
def notifications(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user", "doctor", "admin"))):
    rows = db.query(Notification).filter(Notification.user_id == current.user_id).order_by(Notification.id.desc()).limit(100).all()
    return success([{"id": n.id, "title": n.title, "content": n.content, "type": n.type, "is_read": n.is_read, "create_time": n.create_time} for n in rows])

@router.put("/notifications/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user", "doctor", "admin"))):
    row = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current.user_id).first()
    if not row: raise HTTPException(status_code=404, detail="通知不存在")
    row.is_read = 1; db.commit(); return success(None, "已读")

@router.get("/audit")
def audit(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    q = db.query(AuditLog); total = q.count(); rows = q.order_by(AuditLog.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return page_result([{"id": r.id, "actor_id": r.actor_id, "actor_role": r.actor_role, "action": r.action, "target_type": r.target_type, "target_id": r.target_id, "detail": r.detail, "create_time": r.create_time} for r in rows], total, page, page_size)
