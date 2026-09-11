"""结构化问诊、AI审核与病历摘要模型。"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from db.session import Base


class SymptomAssessment(Base):
    __tablename__ = "t_symptom_assessment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(Integer, index=True)
    symptoms_json = Column(Text, nullable=False)
    onset_time = Column(String(100))
    duration = Column(String(100))
    severity = Column(Integer, default=1)
    temperature = Column(String(20))
    extra_json = Column(Text)
    create_time = Column(DateTime, server_default=func.now())


class AIConsultReview(Base):
    __tablename__ = "t_ai_consult_review"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False, index=True)
    consult_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    doctor_id = Column(Integer)
    ai_summary = Column(Text, nullable=False)
    review_status = Column(Integer, default=0, nullable=False, comment="0待审核1通过2修订")
    doctor_comment = Column(Text)
    record_id = Column(Integer)
    create_time = Column(DateTime, server_default=func.now())
    review_time = Column(DateTime)
