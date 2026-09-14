"""预约与健康档案ORM模型"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Index, CheckConstraint, func
from db.session import Base


class Appointment(Base):
    """预约挂号表"""

    __tablename__ = "t_appointment"
    __table_args__ = (
        Index("ix_appointment_user_id", "user_id", "id"),
        Index("ix_appointment_doctor_id", "doctor_id", "id"),
        Index("ix_appointment_slot", "doctor_id", "visit_date", "time_slot", "status"),
        Index("ix_appointment_status_date", "status", "visit_date"),
        CheckConstraint("status IN (0, 1, 2, 3, 4)", name="ck_appointment_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False, comment="患者ID")
    doctor_id = Column(Integer, ForeignKey("t_doctor.id", ondelete="RESTRICT"), nullable=False, comment="医生ID")
    department_id = Column(Integer, ForeignKey("t_department.id", ondelete="RESTRICT"), nullable=False, comment="科室ID")
    visit_date = Column(Date, nullable=False, comment="就诊日期")
    time_slot = Column(String(20), nullable=False, comment="时段")
    status = Column(Integer, default=0, comment="状态")
    remark = Column(String(255), comment="备注")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class HealthRecord(Base):
    """健康档案表"""

    __tablename__ = "t_health_record"
    __table_args__ = (
        Index("ix_health_record_user_id", "user_id", "id"),
        Index("ix_health_record_doctor_id", "doctor_id", "id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False, comment="患者ID")
    doctor_id = Column(Integer, ForeignKey("t_doctor.id", ondelete="SET NULL"), comment="医生ID")
    record_type = Column(String(50), comment="档案类型")
    diagnosis = Column(String(255), comment="诊断结果")
    treatment = Column(Text, comment="治疗方案")
    prescription = Column(Text, comment="处方")
    visit_date = Column(Date, comment="就诊日期")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
