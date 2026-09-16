"""患者表增加微信 openid / unionid。"""
from alembic import op
import sqlalchemy as sa

revision = "0004_wechat_user"
down_revision = "0003_ai_quality"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def upgrade() -> None:
    columns = {item["name"] for item in _inspector().get_columns("t_user")}
    if "wx_openid" not in columns:
        op.add_column("t_user", sa.Column("wx_openid", sa.String(64), nullable=True, comment="微信小程序 openid"))
    if "wx_unionid" not in columns:
        op.add_column("t_user", sa.Column("wx_unionid", sa.String(64), nullable=True, comment="微信 unionid"))
    indexes = {item["name"] for item in _inspector().get_indexes("t_user")}
    if "uk_user_wx_openid" not in indexes and "ix_t_user_wx_openid" not in indexes:
        op.create_index("uk_user_wx_openid", "t_user", ["wx_openid"], unique=True)
    if "ix_t_user_wx_unionid" not in indexes:
        op.create_index("ix_t_user_wx_unionid", "t_user", ["wx_unionid"], unique=False)


def downgrade() -> None:
    indexes = {item["name"] for item in _inspector().get_indexes("t_user")}
    if "ix_t_user_wx_unionid" in indexes:
        op.drop_index("ix_t_user_wx_unionid", table_name="t_user")
    if "uk_user_wx_openid" in indexes:
        op.drop_index("uk_user_wx_openid", table_name="t_user")
    columns = {item["name"] for item in _inspector().get_columns("t_user")}
    if "wx_unionid" in columns:
        op.drop_column("t_user", "wx_unionid")
    if "wx_openid" in columns:
        op.drop_column("t_user", "wx_openid")
