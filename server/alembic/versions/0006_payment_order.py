from alembic import op
import sqlalchemy as sa
revision="0006_payment_order"; down_revision="0005_appointment_waitlist"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("t_payment_order", sa.Column("id",sa.Integer,primary_key=True),sa.Column("order_no",sa.String(64),nullable=False),sa.Column("user_id",sa.Integer,nullable=False),sa.Column("business_type",sa.String(30),nullable=False),sa.Column("business_id",sa.Integer),sa.Column("amount",sa.Integer,nullable=False,server_default="0"),sa.Column("status",sa.String(20),nullable=False,server_default="pending"),sa.Column("provider",sa.String(20),nullable=False,server_default="wechat"),sa.Column("transaction_id",sa.String(100)),sa.Column("create_time",sa.DateTime,server_default=sa.func.now()),sa.Column("paid_time",sa.DateTime),sa.UniqueConstraint("order_no",name="uq_payment_order_no"))
def downgrade(): op.drop_table("t_payment_order")
