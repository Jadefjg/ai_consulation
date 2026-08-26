"""患者用户ORM模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from db.session import Base


class User(Base):
    """患者用户表"""

    __tablename__ = "t_user"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")
    real_name = Column(String(50), comment="用户昵称")
    gender = Column(Integer, default=1, comment="性别:1男2女")
    age = Column(Integer, comment="年龄")
    phone = Column(String(20), comment="手机号")
    avatar = Column(String(255), comment="头像路径")
    allergy_history = Column(Text, comment="过敏史")
    status = Column(Integer, default=1, comment="状态")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
