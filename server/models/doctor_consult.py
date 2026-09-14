"""人工问诊ORM模型"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index, CheckConstraint, func
from db.session import Base


class DoctorConsult(Base):
    """人工问诊工单表"""

    __tablename__ = "t_doctor_consult"
    __table_args__ = (
        Index("ix_doctor_consult_user_id", "user_id", "id"),
        Index("ix_doctor_consult_doctor_status", "doctor_id", "status", "id"),
        Index("ix_doctor_consult_status_created", "status", "create_time"),
        CheckConstraint("status IN (0, 1, 2, 3)", name="ck_doctor_consult_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False, comment="患者ID")
    doctor_id = Column(Integer, ForeignKey("t_doctor.id", ondelete="SET NULL"), comment="医生ID")
    chief_complaint = Column(Text, nullable=False, comment="主诉")
    status = Column(Integer, default=0, comment="状态:0待处理1已回复2已关闭3超时")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class DoctorReply(Base):
    """医生回复表"""

    __tablename__ = "t_doctor_reply"
    __table_args__ = (Index("ix_doctor_reply_consult_id", "consult_id", "id"),)

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    consult_id = Column(Integer, ForeignKey("t_doctor_consult.id", ondelete="CASCADE"), nullable=False, comment="工单ID")
    doctor_id = Column(Integer, ForeignKey("t_doctor.id", ondelete="RESTRICT"), nullable=False, comment="医生ID")
    content = Column(Text, nullable=False, comment="回复内容")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")


class DoctorConsultFollowup(Base):
    """患者在已回复工单上的追问消息。"""

    __tablename__ = "t_doctor_consult_followup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    consult_id = Column(Integer, ForeignKey("t_doctor_consult.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, server_default=func.now())
