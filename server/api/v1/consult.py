"""人工问诊接口"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.response import success, page_result
from db.session import get_db
from models.doctor_consult import DoctorConsult, DoctorReply
from models.user import User
from models.doctor import Doctor
from schemas.common import DoctorConsultCreate, DoctorReplyCreate
from utils.helpers import format_datetime

router = APIRouter()


@router.post("/create")
def create_consult(req: DoctorConsultCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """患者发起人工问诊"""
    if not (req.chief_complaint or "").strip():
        raise HTTPException(status_code=400, detail="请填写主诉内容")
    doctor_id = req.doctor_id
    if doctor_id is not None:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.status == 1).first()
        if not doctor:
            raise HTTPException(status_code=400, detail="医生不存在或已停用")
    consult = DoctorConsult(
        user_id=current.user_id,
        doctor_id=doctor_id,
        chief_complaint=req.chief_complaint.strip(),
    )
    db.add(consult)
    db.commit()
    return success({"id": consult.id}, "问诊提交成功")


@router.get("/my")
def my_consults(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """患者查看自己的问诊"""
    items = db.query(DoctorConsult).filter(DoctorConsult.user_id == current.user_id).order_by(DoctorConsult.id.desc()).all()
    doctor_ids = {c.doctor_id for c in items if c.doctor_id}
    doctor_map = {
        d.id: d.real_name
        for d in db.query(Doctor).filter(Doctor.id.in_(doctor_ids)).all()
    } if doctor_ids else {}
    consult_ids = [c.id for c in items]
    all_replies = (
        db.query(DoctorReply).filter(DoctorReply.consult_id.in_(consult_ids)).all()
        if consult_ids else []
    )
    reply_map: dict[int, list] = {}
    for reply in all_replies:
        reply_map.setdefault(reply.consult_id, []).append(reply)
    data = []
    for c in items:
        replies = reply_map.get(c.id, [])
        data.append({
            "id": c.id, "doctor_id": c.doctor_id, "doctor_name": doctor_map.get(c.doctor_id, "待分配"),
            "chief_complaint": c.chief_complaint, "status": c.status,
            "create_time": format_datetime(c.create_time),
            "replies": [{"content": r.content, "create_time": format_datetime(r.create_time)} for r in replies],
        })
    return success(data)


@router.get("/doctor/pending")
def doctor_pending(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("doctor"))):
    """医生待回复列表"""
    items = db.query(DoctorConsult).filter(
        (DoctorConsult.doctor_id == current.user_id) | (DoctorConsult.doctor_id.is_(None)),
        DoctorConsult.status == 0,
    ).order_by(DoctorConsult.id.desc()).all()
    user_ids = {c.user_id for c in items}
    user_map = {
        u.id: u.real_name or u.username
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}
    data = [{
        "id": c.id, "user_id": c.user_id, "user_name": user_map.get(c.user_id, ""),
        "chief_complaint": c.chief_complaint, "create_time": format_datetime(c.create_time),
    } for c in items]
    return success(data)


@router.post("/reply")
def doctor_reply(req: DoctorReplyCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("doctor"))):
    """医生回复（仅本人工单或未分配工单，行级锁防并发抢单）"""
    consult = (
        db.query(DoctorConsult)
        .filter(DoctorConsult.id == req.consult_id)
        .with_for_update()
        .first()
    )
    if not consult:
        raise HTTPException(status_code=404, detail="工单不存在")
    if consult.doctor_id is not None and consult.doctor_id != current.user_id:
        raise HTTPException(status_code=403, detail="无权回复其他医生的工单")
    if not (req.content or "").strip():
        raise HTTPException(status_code=400, detail="回复内容不能为空")
    if not consult.doctor_id:
        consult.doctor_id = current.user_id
    reply = DoctorReply(consult_id=req.consult_id, doctor_id=current.user_id, content=req.content.strip())
    consult.status = 1
    db.add(reply)
    db.commit()
    return success(None, "回复成功")


@router.get("/admin/list")
def admin_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    status: int = Query(None),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员工单列表（支持搜索与分页）"""
    q = db.query(DoctorConsult)
    if keyword:
        q = (
            q.outerjoin(User, DoctorConsult.user_id == User.id)
            .outerjoin(Doctor, DoctorConsult.doctor_id == Doctor.id)
            .filter(
                or_(
                    DoctorConsult.chief_complaint.contains(keyword),
                    User.username.contains(keyword),
                    User.real_name.contains(keyword),
                    Doctor.real_name.contains(keyword),
                )
            )
            .distinct()
        )
    if status is not None:
        q = q.filter(DoctorConsult.status == status)
    total = q.count()
    items = q.order_by(DoctorConsult.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    user_ids = {c.user_id for c in items}
    doctor_ids = {c.doctor_id for c in items if c.doctor_id}
    user_map = {
        u.id: u.real_name or u.username
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}
    doctor_map = {
        d.id: d.real_name
        for d in db.query(Doctor).filter(Doctor.id.in_(doctor_ids)).all()
    } if doctor_ids else {}
    data = [{
        "id": c.id, "user_name": user_map.get(c.user_id, ""), "doctor_name": doctor_map.get(c.doctor_id, "待分配"),
        "chief_complaint": c.chief_complaint, "status": c.status,
        "create_time": format_datetime(c.create_time),
    } for c in items]
    return page_result(data, total, page, page_size)


@router.delete("/admin/{consult_id}")
def admin_delete_consult(
    consult_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员删除咨询工单"""
    consult = db.query(DoctorConsult).filter(DoctorConsult.id == consult_id).first()
    if not consult:
        raise HTTPException(status_code=404, detail="咨询记录不存在")
    db.query(DoctorReply).filter(DoctorReply.consult_id == consult_id).delete(synchronize_session=False)
    db.delete(consult)
    db.commit()
    return success(None, "删除成功")
