from alembic import op
import sqlalchemy as sa
revision = "0005_appointment_waitlist"
down_revision = "0004_wechat_user"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("t_appointment_waitlist", sa.Column("id",sa.Integer,primary_key=True), sa.Column("user_id",sa.Integer,nullable=False), sa.Column("doctor_id",sa.Integer,nullable=False), sa.Column("work_date",sa.Date,nullable=False), sa.Column("time_slot",sa.String(20),nullable=False), sa.Column("status",sa.Integer,nullable=False,server_default="0"), sa.Column("create_time",sa.DateTime,server_default=sa.func.now()), sa.UniqueConstraint("user_id","doctor_id","work_date","time_slot",name="uq_waitlist_entry"))
def downgrade(): op.drop_table("t_appointment_waitlist")
