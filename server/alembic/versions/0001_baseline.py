"""建立项目结构基线。"""
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 对新库创建完整结构；对已有库保持数据并仅补缺失表。
    from db.session import Base
    import models  # noqa: F401
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    # 基线降级不自动删除业务表，防止误删存量数据。
    pass

