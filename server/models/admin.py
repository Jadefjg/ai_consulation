"""管理员ORM模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from db.session import Base


class Admin(Base):
    """管理员表"""

    __tablename__ = "t_admin"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")
    nickname = Column(String(50), comment="昵称")
    avatar = Column(String(255), comment="头像路径")
    phone = Column(String(20), comment="手机号")
    email = Column(String(100), comment="邮箱")
    status = Column(Integer, default=1, comment="状态")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
