"""人工问诊ORM模型"""
from sqlalchemy import Column, Integer, Text, DateTime, func
from db.session import Base


class DoctorConsult(Base):
    """人工问诊工单表"""

    __tablename__ = "t_doctor_consult"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, nullable=False, comment="患者ID")
    doctor_id = Column(Integer, comment="医生ID")
    chief_complaint = Column(Text, nullable=False, comment="主诉")
    status = Column(Integer, default=0, comment="状态:0待处理1已回复2已关闭3超时")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class DoctorReply(Base):
    """医生回复表"""

    __tablename__ = "t_doctor_reply"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    consult_id = Column(Integer, nullable=False, comment="工单ID")
    doctor_id = Column(Integer, nullable=False, comment="医生ID")
    content = Column(Text, nullable=False, comment="回复内容")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")


class DoctorConsultFollowup(Base):
    """患者在已回复工单上的追问消息。"""

    __tablename__ = "t_doctor_consult_followup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    consult_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, server_default=func.now())
