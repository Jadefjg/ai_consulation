"""AI问诊ORM模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, CheckConstraint, func
from db.session import Base


class ConsultSession(Base):
    """AI问诊会话表"""

    __tablename__ = "t_consult_session"
    __table_args__ = (Index("ix_consult_session_user_updated", "user_id", "update_time"),)

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("t_user.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    title = Column(String(200), default="新会话", comment="会话标题")
    message_count = Column(Integer, default=0, comment="消息数量")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class ConsultMessage(Base):
    """AI问诊消息表"""

    __tablename__ = "t_consult_message"
    __table_args__ = (
        Index("ix_consult_message_session_id", "session_id", "id"),
        CheckConstraint("delivery_status IN ('pending', 'completed', 'failed', 'cancelled')", name="ck_message_delivery_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    session_id = Column(Integer, ForeignKey("t_consult_session.id", ondelete="CASCADE"), nullable=False, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色")
    content = Column(Text, nullable=False, comment="消息内容")
    references_json = Column(Text, comment="引用来源JSON")
    graph_json = Column(Text, comment="图谱实体JSON")
    cost_time = Column(Integer, default=0, comment="耗时毫秒")
    delivery_status = Column(String(20), default="completed", nullable=False, comment="生成状态")
    error_message = Column(String(500), comment="失败或取消原因")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
