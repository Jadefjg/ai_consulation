"""科室ORM模型"""
from sqlalchemy import Column, Integer, String, DateTime, func
from db.session import Base


class Department(Base):
    """科室表"""

    __tablename__ = "t_department"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(50), nullable=False, comment="科室名称")
    description = Column(String(255), comment="科室描述")
    sort_order = Column(Integer, default=0, comment="排序")
    status = Column(Integer, default=1, comment="状态")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
