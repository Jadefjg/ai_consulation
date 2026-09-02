"""用户管理接口"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.response import success, page_result
from db.session import get_db
from models.user import User
from models.doctor import Doctor
from models.admin import Admin
from models.appointment import Appointment, HealthRecord
from models.consult import ConsultSession, ConsultMessage
from models.doctor_consult import DoctorConsult, DoctorReply
from schemas.common import UserCreate, UserUpdate
from core.security import hash_password
from utils.account import username_exists
from utils.helpers import format_datetime

router = APIRouter()

_ROLE_LABELS = {"user": "用户", "doctor": "医生", "admin": "管理员", "root": "超级管理员"}
_ROLE_SORT_ORDER = {"root": 0, "admin": 1, "doctor": 2, "user": 3}


def _user_to_dict(user: User) -> dict:
    """将用户对象转为字典"""
    data = {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "gender": user.gender,
        "age": user.age,
        "phone": user.phone,
        "avatar": user.avatar,
        "allergy_history": user.allergy_history,
        "status": user.status,
        "create_time": format_datetime(user.create_time),
        "role": "user",
        "role_label": _ROLE_LABELS["user"],
    }
    return data


def _doctor_to_account(doctor: Doctor) -> dict:
    """医生账号转为统一列表项"""
    return {
        "id": doctor.id,
        "username": doctor.username,
        "real_name": doctor.real_name,
        "gender": None,
        "age": None,
        "phone": doctor.phone,
        "avatar": doctor.avatar,
        "allergy_history": None,
        "status": doctor.status,
        "create_time": format_datetime(doctor.create_time),
        "role": "doctor",
        "role_label": _ROLE_LABELS["doctor"],
        "department_id": doctor.department_id,
        "title": doctor.title,
        "specialty": doctor.specialty,
        "introduction": doctor.introduction,
    }


def _admin_to_account(admin: Admin) -> dict:
    """管理员账号转为统一列表项"""
    admin_role = getattr(admin, "admin_role", "admin") or "admin"
    role = "root" if admin_role == "root" else "admin"
    return {
        "id": admin.id,
        "username": admin.username,
        "real_name": admin.nickname,
        "gender": None,
        "age": None,
        "phone": admin.phone,
        "avatar": admin.avatar,
        "allergy_history": None,
        "status": admin.status,
        "create_time": format_datetime(admin.create_time),
        "role": role,
        "role_label": _ROLE_LABELS[role],
        "email": admin.email,
    }


def _match_keyword(keyword: str, username: str, display_name: str, phone: str) -> bool:
    """关键字是否匹配用户名/昵称/手机号"""
    if not keyword:
        return True
    kw = keyword.lower()
    for val in (username, display_name or "", phone or ""):
        if val and kw in val.lower():
            return True
    return False


@router.get("/list")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """账号列表（管理员，聚合用户/医生/管理员，支持搜索与分页）"""
    kw = keyword.strip()

    accounts = []
    for user in db.query(User).all():
        if _match_keyword(kw, user.username, user.real_name or "", user.phone or ""):
            accounts.append(_user_to_dict(user))
    for doctor in db.query(Doctor).all():
        if _match_keyword(kw, doctor.username, doctor.real_name or "", doctor.phone or ""):
            accounts.append(_doctor_to_account(doctor))
    for admin in db.query(Admin).all():
        if _match_keyword(kw, admin.username, admin.nickname or "", admin.phone or ""):
            accounts.append(_admin_to_account(admin))

    accounts.sort(key=lambda x: x.get("create_time") or "", reverse=True)
    accounts.sort(key=lambda x: _ROLE_SORT_ORDER.get(x.get("role"), 9))
    total = len(accounts)
    start = (page - 1) * page_size
    data = accounts[start : start + page_size]
    for index, item in enumerate(data):
        item["seq"] = start + index + 1
    return page_result(data, total, page, page_size)


@router.post("/create")
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员创建用户"""
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次密码输入不一致")
    if username_exists(db, req.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=req.username,
        password=hash_password(req.password),
        real_name=req.real_name,
        gender=req.gender,
        age=req.age,
        phone=req.phone,
        allergy_history=req.allergy_history,
        status=req.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success(_user_to_dict(user), "创建成功")


@router.put("/{user_id}")
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.password:
        if not req.confirm_password:
            raise HTTPException(status_code=400, detail="请填写确认密码")
        if req.password != req.confirm_password:
            raise HTTPException(status_code=400, detail="两次密码输入不一致")
        user.password = hash_password(req.password)
    if req.real_name is not None:
        user.real_name = req.real_name
    if req.gender is not None:
        user.gender = req.gender
    if req.age is not None:
        user.age = req.age
    if req.phone is not None:
        user.phone = req.phone
    if req.allergy_history is not None:
        user.allergy_history = req.allergy_history
    if req.status is not None:
        user.status = req.status
    db.commit()
    db.refresh(user)
    return success(_user_to_dict(user), "更新成功")


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员删除用户（同时清理关联数据）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 清理 AI 问诊会话及消息
    session_ids = [
        s.id for s in db.query(ConsultSession).filter(ConsultSession.user_id == user_id).all()
    ]
    if session_ids:
        db.query(ConsultMessage).filter(ConsultMessage.session_id.in_(session_ids)).delete(
            synchronize_session=False
        )
        db.query(ConsultSession).filter(ConsultSession.user_id == user_id).delete(
            synchronize_session=False
        )

    # 清理人工问诊及回复
    consult_ids = [
        c.id for c in db.query(DoctorConsult).filter(DoctorConsult.user_id == user_id).all()
    ]
    if consult_ids:
        db.query(DoctorReply).filter(DoctorReply.consult_id.in_(consult_ids)).delete(
            synchronize_session=False
        )
        db.query(DoctorConsult).filter(DoctorConsult.user_id == user_id).delete(
            synchronize_session=False
        )

    # 清理预约与健康档案
    db.query(Appointment).filter(Appointment.user_id == user_id).delete(synchronize_session=False)
    db.query(HealthRecord).filter(HealthRecord.user_id == user_id).delete(synchronize_session=False)

    db.delete(user)
    db.commit()
    return success(None, "删除成功")


@router.put("/{user_id}/status")
def toggle_status(
    user_id: int,
    status: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """切换用户状态"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if status not in (0, 1):
        raise HTTPException(status_code=400, detail="状态值无效")
    user.status = status
    db.commit()
    return success(None, "状态更新成功")
