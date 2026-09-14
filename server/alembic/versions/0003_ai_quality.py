"""AI 回复质量与安全评估记录。"""
from alembic import op
import sqlalchemy as sa

revision = "0003_ai_quality"
down_revision = "0002_phase2_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "t_ai_response_evaluation" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "t_ai_response_evaluation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("message_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("safety_level", sa.String(20), nullable=False),
        sa.Column("safety_action", sa.String(30), nullable=False),
        sa.Column("citation_coverage", sa.String(20), nullable=False),
        sa.Column("groundedness", sa.String(20), nullable=False),
        sa.Column("disclaimer_present", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("details_json", sa.Text()),
        sa.Column("create_time", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["message_id"], ["t_consult_message.id"], name="fk_evaluation_message", ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("t_ai_response_evaluation")
