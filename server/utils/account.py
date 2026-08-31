"""账号相关工具"""
from sqlalchemy.orm import Session

from models.admin import Admin
from models.doctor import Doctor
from models.user import User


def username_exists(db: Session, username: str) -> bool:
    """检查用户名是否已在任一角色表中存在"""
    return bool(
        db.query(User).filter(User.username == username).first()
        or db.query(Doctor).filter(Doctor.username == username).first()
        or db.query(Admin).filter(Admin.username == username).first()
    )
