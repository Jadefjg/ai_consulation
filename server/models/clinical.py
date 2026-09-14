"""结构化问诊、AI审核与病历摘要模型。"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, func
from db.session import Base


class SymptomAssessment(Base):
    __tablename__ = "t_symptom_assessment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("t_consult_session.id", ondelete="SET NULL"), index=True)
    symptoms_json = Column(Text, nullable=False)
    onset_time = Column(String(100))
    duration = Column(String(100))
    severity = Column(Integer, default=1)
    temperature = Column(String(20))
    extra_json = Column(Text)
    create_time = Column(DateTime, server_default=func.now())


class AIConsultReview(Base):
    __tablename__ = "t_ai_consult_review"
    __table_args__ = (CheckConstraint("review_status IN (0, 1, 2)", name="ck_ai_review_status"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("t_consult_session.id", ondelete="CASCADE"), nullable=False, index=True)
    consult_id = Column(Integer, ForeignKey("t_doctor_consult.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("t_doctor.id", ondelete="SET NULL"))
    ai_summary = Column(Text, nullable=False)
    review_status = Column(Integer, default=0, nullable=False, comment="0待审核1通过2修订")
    doctor_comment = Column(Text)
    record_id = Column(Integer)
    create_time = Column(DateTime, server_default=func.now())
    review_time = Column(DateTime)


class AIResponseEvaluation(Base):
    """每次 AI 回复的自动质量与安全评估。"""

    __tablename__ = "t_ai_response_evaluation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("t_consult_message.id", ondelete="CASCADE"), nullable=False, unique=True)
    safety_level = Column(String(20), nullable=False)
    safety_action = Column(String(30), nullable=False)
    citation_coverage = Column(String(20), nullable=False)
    groundedness = Column(String(20), nullable=False)
    disclaimer_present = Column(Integer, nullable=False, default=0)
    details_json = Column(Text)
    create_time = Column(DateTime, server_default=func.now())
