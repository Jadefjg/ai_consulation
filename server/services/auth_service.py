"""认证服务"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.security import (
    verify_password,
    create_access_token,
    hash_password,
    is_password_hashed,
)
from core.roles import ROOT_ROLE, ADMIN_ROLE
from models.admin import Admin
from models.department import Department
from models.doctor import Doctor
from models.user import User
from schemas.common import LoginRequest, RegisterRequest, TokenResponse
from utils.account import username_exists

_PUBLIC_REGISTER_ROLES = {"user", "doctor", "admin"}


class AuthService:
    """认证业务逻辑"""

    _ROLE_LABELS = {"user": "用户", "doctor": "医生", "admin": "管理员", "root": "超级管理员"}

    @staticmethod
    def _admin_token_role(admin: Admin) -> str:
        """根据管理员类型返回 JWT 角色"""
        if getattr(admin, "admin_role", ADMIN_ROLE) == ROOT_ROLE:
            return ROOT_ROLE
        return ADMIN_ROLE

    @staticmethod
    def _find_matching_account(db: Session, username: str, password: str):
        """
        跨角色表查找用户名密码匹配的账号
        :return: (role, account, nickname) 或 (None, None, None)
        """
        candidates = [
            ("user", User, lambda obj: obj.real_name),
            ("doctor", Doctor, lambda obj: obj.real_name),
        ]
        for role, model, get_nickname in candidates:
            obj = db.query(model).filter(model.username == username).first()
            if obj and verify_password(password, obj.password):
                return role, obj, get_nickname(obj)
        admin = db.query(Admin).filter(Admin.username == username).first()
        if admin and verify_password(password, admin.password):
            token_role = AuthService._admin_token_role(admin)
            return token_role, admin, admin.nickname
        return None, None, None

    @staticmethod
    def _validate_department(db: Session, department_id: int) -> None:
        """校验科室存在且启用"""
        dept = db.query(Department).filter(Department.id == department_id, Department.status == 1).first()
        if not dept:
            raise HTTPException(status_code=400, detail="科室不存在或已停用")

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
            actual_role, _, _ = AuthService._find_matching_account(db, req.username, req.password)
            if actual_role and actual_role != req.role and not (
                req.role == ADMIN_ROLE and actual_role == ROOT_ROLE
            ):
                label = AuthService._ROLE_LABELS.get(actual_role, actual_role)
                raise HTTPException(
                    status_code=401,
                    detail=f"登录身份不正确，该账号为「{label}」账号，请选择对应身份登录",
                )
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        if hasattr(user, "status") and user.status == 0:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        # 登录成功后把历史明文密码升级为哈希
        if not is_password_hashed(user.password):
            user.password = hash_password(req.password)
            db.commit()

        token_role = AuthService._admin_token_role(user) if req.role == ADMIN_ROLE else req.role
        token = create_access_token({
            "sub": user.username,
            "user_id": user.id,
            "role": token_role,
        })
        return TokenResponse(
            access_token=token,
            role=token_role,
            user_id=user.id,
            username=user.username,
            nickname=nickname,
            avatar=getattr(user, "avatar", None),
        )

    @staticmethod
    def register(db: Session, req: RegisterRequest) -> TokenResponse:
        """
        三角色公开注册（用户/医生/管理员）
        """
        role = req.role or "user"
        if role not in _PUBLIC_REGISTER_ROLES:
            raise HTTPException(status_code=400, detail="无效的角色类型")
        if req.password != req.confirm_password:
            raise HTTPException(status_code=400, detail="两次密码输入不一致")
        if username_exists(db, req.username):
            raise HTTPException(status_code=400, detail="用户名已存在")

        hashed = hash_password(req.password)
        display_name = (req.real_name or req.username).strip()

        if role == "admin":
            account = Admin(
                username=req.username,
                password=hashed,
                nickname=display_name,
                phone=req.phone,
                admin_role=ADMIN_ROLE,
                status=1,
            )
            nickname = display_name
        elif role == "doctor":
            if req.department_id is None:
                raise HTTPException(status_code=400, detail="请选择所属科室")
            AuthService._validate_department(db, req.department_id)
            account = Doctor(
                username=req.username,
                password=hashed,
                real_name=display_name,
                department_id=req.department_id,
                title=req.title,
                specialty=req.specialty,
                phone=req.phone,
                status=1,
            )
            nickname = display_name
        else:
            account = User(
                username=req.username,
                password=hashed,
                real_name=display_name,
                phone=req.phone,
                gender=1,
            )
            nickname = display_name

        db.add(account)
        db.commit()
        db.refresh(account)
        token_role = role
        token = create_access_token({"sub": account.username, "user_id": account.id, "role": token_role})
        return TokenResponse(
            access_token=token,
            role=token_role,
            user_id=account.id,
            username=account.username,
            nickname=nickname,
        )
