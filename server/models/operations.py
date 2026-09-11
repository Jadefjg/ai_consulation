"""运营扩展模型：排班、通知与审计。"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, func
from db.session import Base


class DoctorSchedule(Base):
    __tablename__ = "t_doctor_schedule"
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, nullable=False)
    work_date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=False)
    capacity = Column(Integer, default=1, nullable=False)
    status = Column(Integer, default=1, nullable=False)
    create_time = Column(DateTime, server_default=func.now())


class Notification(Base):
    __tablename__ = "t_notification"
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
