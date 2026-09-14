"""运营扩展模型：排班、通知与审计。"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Index, CheckConstraint, UniqueConstraint, func
from db.session import Base


class DoctorSchedule(Base):
    __tablename__ = "t_doctor_schedule"
    __table_args__ = (
        Index("ix_doctor_schedule_date", "doctor_id", "work_date", "status"),
        UniqueConstraint("doctor_id", "work_date", "time_slot", name="uq_doctor_schedule_slot"),
        CheckConstraint("capacity > 0", name="ck_doctor_schedule_capacity"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("t_doctor.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=False)
    capacity = Column(Integer, default=1, nullable=False)
    status = Column(Integer, default=1, nullable=False)
    create_time = Column(DateTime, server_default=func.now())


class Notification(Base):
    __tablename__ = "t_notification"
    __table_args__ = (Index("ix_notification_user_id", "user_id", "id"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(30), default="system")
    is_read = Column(Integer, default=0, nullable=False)
    create_time = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "t_audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, nullable=False)
    actor_role = Column(String(20), nullable=False)
    action = Column(String(80), nullable=False)
    target_type = Column(String(40), nullable=False)
    target_id = Column(Integer)
    detail = Column(Text)
    create_time = Column(DateTime, server_default=func.now())
