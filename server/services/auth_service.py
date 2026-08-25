"""认证服务"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.security import verify_password, create_access_token
from models.admin import Admin
from models.doctor import Doctor
from models.user import User
from schemas.common import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    """认证业务逻辑"""

    @staticmethod
    def login(db: Session, req: LoginRequest) -> TokenResponse:
        """
        三角色登录
        :param req: 登录请求
        :return: 令牌响应
        """
        if req.role == "admin":
            user = db.query(Admin).filter(Admin.username == req.username).first()
            nickname = user.nickname if user else None
        elif req.role == "doctor":
            user = db.query(Doctor).filter(Doctor.username == req.username).first()
            nickname = user.real_name if user else None
        elif req.role == "user":
            user = db.query(User).filter(User.username == req.username).first()
            nickname = user.real_name if user else None
        else:
            raise HTTPException(status_code=400, detail="无效的角色类型")

        if not user or not verify_password(req.password, user.password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        if hasattr(user, "status") and user.status == 0:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        token = create_access_token({
            "sub": user.username,
            "user_id": user.id,
            "role": req.role,
        })
        return TokenResponse(
            access_token=token,
            role=req.role,
            user_id=user.id,
            username=user.username,
            nickname=nickname,
            avatar=getattr(user, "avatar", None),
        )

    @staticmethod
    def register(db: Session, req: RegisterRequest) -> TokenResponse:
        """
        患者注册（含确认密码校验）
        """
        if req.password != req.confirm_password:
            raise HTTPException(status_code=400, detail="两次密码输入不一致")
        existing = db.query(User).filter(User.username == req.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        user = User(
            username=req.username,
            password=req.password,
            real_name=req.real_name,
            phone=req.phone,
            gender=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token({"sub": user.username, "user_id": user.id, "role": "user"})
        return TokenResponse(
            access_token=token,
            role="user",
            user_id=user.id,
            username=user.username,
            nickname=user.real_name,
        )
