"""认证接口"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.response import success
from db.session import get_db
from schemas.common import LoginRequest, RegisterRequest
from services.auth_service import AuthService

router = APIRouter()


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """三角色登录"""
    result = AuthService.login(db, req)
    return success(result.model_dump())


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """患者注册（含确认密码校验）"""
    result = AuthService.register(db, req)
    return success(result.model_dump())
