"""依赖注入模块 - 当前用户与角色守卫"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.security import decode_access_token
from core.roles import ADMIN_PANEL_ROLES, expand_required_roles
from db.session import get_db
from models.admin import Admin
from models.doctor import Doctor
from models.user import User

security = HTTPBearer(auto_error=False)


class CurrentUser:
    """当前登录用户信息"""

    def __init__(self, user_id: int, username: str, role: str, obj=None):
        self.user_id = user_id
        self.username = username
        self.role = role  # user / doctor / admin / root
        self.obj = obj  # ORM对象


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """获取当前登录用户（禁用账号立即失效）"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效或已过期")
    user_id = payload.get("user_id")
    username = payload.get("sub")
    role = payload.get("role")
    if not user_id or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌数据不完整")

    obj = None
    if role in ADMIN_PANEL_ROLES:
        obj = db.query(Admin).filter(Admin.id == user_id).first()
    elif role == "doctor":
        obj = db.query(Doctor).filter(Doctor.id == user_id).first()
    elif role == "user":
        obj = db.query(User).filter(User.id == user_id).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if getattr(obj, "status", 1) == 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return CurrentUser(user_id=user_id, username=username, role=role, obj=obj)


def require_roles(*roles: str):
    """角色守卫装饰器工厂"""

    def role_checker(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current.role not in expand_required_roles(*roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current

    return role_checker
