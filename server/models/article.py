"""文章与公告ORM模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, func
from db.session import Base


class Article(Base):
    """健康科普文章表"""

    __tablename__ = "t_article"
    __table_args__ = (
        Index("ix_article_status_category_id", "status", "category", "id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    title = Column(String(200), nullable=False, comment="文章标题")
    category = Column(String(50), comment="分类")
    cover = Column(String(255), comment="封面图")
    summary = Column(String(500), comment="摘要")
    content = Column(Text, comment="文章内容")
    view_count = Column(Integer, default=0, comment="浏览量")
    status = Column(Integer, default=1, comment="状态")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class Notice(Base):
    """系统公告表"""

    __tablename__ = "t_notice"
    __table_args__ = (Index("ix_notice_status_id", "status", "id"),)

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    title = Column(String(200), nullable=False, comment="公告标题")
    content = Column(Text, comment="公告内容")
    status = Column(Integer, default=1, comment="状态")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
