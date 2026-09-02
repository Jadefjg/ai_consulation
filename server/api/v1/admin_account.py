"""管理员账号管理（仅超级管理员）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.response import success
from core.security import hash_password
from db.session import get_db
from models.admin import Admin
from schemas.common import AdminCreate, AdminUpdate
from utils.account import username_exists
from utils.helpers import format_datetime

router = APIRouter()


def _admin_to_dict(admin: Admin) -> dict:
    admin_role = getattr(admin, "admin_role", "admin") or "admin"
    role = "root" if admin_role == "root" else "admin"
    return {
        "id": admin.id,
        "username": admin.username,
        "real_name": admin.nickname,
        "nickname": admin.nickname,
        "phone": admin.phone,
        "email": admin.email,
        "avatar": admin.avatar,
        "status": admin.status,
        "role": role,
        "role_label": "超级管理员" if role == "root" else "管理员",
        "create_time": format_datetime(admin.create_time),
    }


def _ensure_mutable_target(admin: Admin, current: CurrentUser) -> None:
    """禁止操作超级管理员账号或当前登录账号"""
    admin_role = getattr(admin, "admin_role", "admin") or "admin"
    if admin_role == "root":
        raise HTTPException(status_code=403, detail="不能操作超级管理员账号")
    if admin.id == current.user_id:
        raise HTTPException(status_code=403, detail="不能操作当前登录账号")


@router.post("/create")
def create_admin(
    req: AdminCreate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("root")),
):
    """超级管理员创建普通管理员"""
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次密码输入不一致")
    if username_exists(db, req.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    admin = Admin(
        username=req.username,
        password=hash_password(req.password),
        nickname=req.nickname,
        phone=req.phone,
        email=req.email,
        status=req.status,
        admin_role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return success(_admin_to_dict(admin), "创建成功")


@router.put("/{admin_id}")
def update_admin(
    admin_id: int,
    req: AdminUpdate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_roles("root")),
):
    """超级管理员更新管理员"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    _ensure_mutable_target(admin, current)
    if req.password:
        if not req.confirm_password:
            raise HTTPException(status_code=400, detail="请填写确认密码")
        if req.password != req.confirm_password:
            raise HTTPException(status_code=400, detail="两次密码输入不一致")
        admin.password = hash_password(req.password)
    if req.nickname is not None:
        admin.nickname = req.nickname
    if req.phone is not None:
        admin.phone = req.phone
    if req.email is not None:
        admin.email = req.email
    if req.status is not None:
        admin.status = req.status
    db.commit()
    db.refresh(admin)
    return success(_admin_to_dict(admin), "更新成功")


@router.delete("/{admin_id}")
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_roles("root")),
):
    """超级管理员删除管理员"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    _ensure_mutable_target(admin, current)
    db.delete(admin)
    db.commit()
    return success(None, "删除成功")


@router.put("/{admin_id}/status")
def toggle_admin_status(
    admin_id: int,
    status: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_roles("root")),
):
    """超级管理员切换管理员状态"""
    if status not in (0, 1):
        raise HTTPException(status_code=400, detail="状态值无效")
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    _ensure_mutable_target(admin, current)
    admin.status = status
    db.commit()
    return success(None, "状态更新成功")
