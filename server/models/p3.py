"""P3 随访、慢病、风险与知识库审核模型。"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, func
from db.session import Base

class FollowupPlan(Base):
    __tablename__ = "t_followup_plan"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    doctor_id = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    frequency_days = Column(Integer, default=30, nullable=False)
    next_date = Column(Date, nullable=False)
    status = Column(Integer, default=1, nullable=False, comment="1进行中2暂停3完成")
    notes = Column(Text)
    create_time = Column(DateTime, server_default=func.now())

class FollowupTask(Base):
    __tablename__ = "t_followup_task"
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, nullable=False, index=True)
    due_date = Column(Date, nullable=False)
    response = Column(Text)
    status = Column(Integer, default=0, nullable=False, comment="0待完成1已完成2逾期")
    completed_time = Column(DateTime)

class ChronicRecord(Base):
    __tablename__ = "t_chronic_record"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    doctor_id = Column(Integer)
    disease = Column(String(100), nullable=False)
    target_json = Column(Text)
    status = Column(Integer, default=1, nullable=False)
    create_time = Column(DateTime, server_default=func.now())

class ChronicMetric(Base):
    __tablename__ = "t_chronic_metric"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chronic_id = Column(Integer, nullable=False, index=True)
    metric = Column(String(50), nullable=False)
    value = Column(String(100), nullable=False)
    measured_at = Column(DateTime, server_default=func.now())

class RiskAssessment(Base):
    __tablename__ = "t_risk_assessment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    source = Column(String(30), default="rule")
    score = Column(Integer, nullable=False)
    level = Column(String(20), nullable=False)
    factors_json = Column(Text)
    create_time = Column(DateTime, server_default=func.now())

class KnowledgeVersion(Base):
    __tablename__ = "t_knowledge_version"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    status = Column(Integer, default=0, nullable=False, comment="0待审核1已发布2驳回")
    reviewer_id = Column(Integer)
    review_comment = Column(Text)
    create_time = Column(DateTime, server_default=func.now())
