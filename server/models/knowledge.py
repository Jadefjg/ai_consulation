"""知识库ORM模型"""
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, ForeignKey, Index, CheckConstraint, func
from db.session import Base


class KnowledgeFile(Base):
    """知识库文件表"""

    __tablename__ = "t_knowledge_file"
    __table_args__ = (
        CheckConstraint("vector_status IN (0, 1, 2, 3)", name="ck_knowledge_vector_status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_type = Column(String(20), nullable=False, comment="文件类型")
    file_size = Column(BigInteger, default=0, comment="文件大小")
    file_path = Column(String(500), nullable=False, comment="存储路径")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    vector_status = Column(Integer, default=0, comment="向量化状态")
    vector_task_id = Column(String(64), comment="异步任务ID")
    vector_error = Column(String(1000), comment="最近一次向量化错误")
    upload_by = Column(Integer, comment="上传人ID")
    upload_role = Column(String(20), default="admin", comment="上传人角色")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class KnowledgeChunk(Base):
    """知识库分块表"""

    __tablename__ = "t_knowledge_chunk"
    __table_args__ = (
        Index("ix_knowledge_chunk_file_id", "file_id", "chunk_index"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    file_id = Column(Integer, ForeignKey("t_knowledge_file.id", ondelete="CASCADE"), nullable=False, comment="文件ID")
    chunk_index = Column(Integer, nullable=False, comment="分块序号")
    content = Column(Text, nullable=False, comment="分块内容")
    vector_id = Column(String(100), comment="Chroma向量ID")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
