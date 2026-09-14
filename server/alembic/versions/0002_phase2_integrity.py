"""异步状态字段、外键及一致性约束。"""
from alembic import op
import sqlalchemy as sa

revision = "0002_phase2_integrity"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _add_column(table: str, column: sa.Column) -> None:
    if column.name not in {item["name"] for item in _inspector().get_columns(table)}:
        op.add_column(table, column)


def _add_fk(name: str, table: str, columns: list[str], target: str, remote: list[str], ondelete: str) -> None:
    existing = {fk.get("name") for fk in _inspector().get_foreign_keys(table)}
    if name in existing:
        return
    join = " AND ".join(f"c.{col} = p.{ref}" for col, ref in zip(columns, remote))
    null_guard = " AND ".join(f"c.{col} IS NOT NULL" for col in columns)
    count = op.get_bind().execute(sa.text(
        f"SELECT COUNT(*) FROM {table} c LEFT JOIN {target} p ON {join} WHERE {null_guard} AND p.{remote[0]} IS NULL"
    )).scalar_one()
    if count:
        raise RuntimeError(f"无法添加外键 {name}: {table} 存在 {count} 条孤儿数据")
    op.create_foreign_key(name, table, target, columns, remote, ondelete=ondelete)


def _add_check(name: str, table: str, expression: str) -> None:
    if name not in {item.get("name") for item in _inspector().get_check_constraints(table)}:
        op.create_check_constraint(name, table, expression)


def upgrade() -> None:
    _add_column("t_knowledge_file", sa.Column("vector_task_id", sa.String(64), nullable=True))
    _add_column("t_knowledge_file", sa.Column("vector_error", sa.String(1000), nullable=True))
    _add_column("t_consult_message", sa.Column("delivery_status", sa.String(20), nullable=False, server_default="completed"))
    _add_column("t_consult_message", sa.Column("error_message", sa.String(500), nullable=True))

    # SQLite 的基线建表已包含约束；ALTER TABLE 不支持后续追加外键，生产 MySQL 继续执行下面的校验。
    if op.get_bind().dialect.name == "sqlite":
        return

    foreign_keys = [
        ("fk_doctor_department", "t_doctor", ["department_id"], "t_department", ["id"], "SET NULL"),
        ("fk_chunk_file", "t_knowledge_chunk", ["file_id"], "t_knowledge_file", ["id"], "CASCADE"),
        ("fk_session_user", "t_consult_session", ["user_id"], "t_user", ["id"], "CASCADE"),
        ("fk_message_session", "t_consult_message", ["session_id"], "t_consult_session", ["id"], "CASCADE"),
        ("fk_consult_user", "t_doctor_consult", ["user_id"], "t_user", ["id"], "CASCADE"),
        ("fk_consult_doctor", "t_doctor_consult", ["doctor_id"], "t_doctor", ["id"], "SET NULL"),
        ("fk_reply_consult", "t_doctor_reply", ["consult_id"], "t_doctor_consult", ["id"], "CASCADE"),
        ("fk_reply_doctor", "t_doctor_reply", ["doctor_id"], "t_doctor", ["id"], "RESTRICT"),
        ("fk_appointment_user", "t_appointment", ["user_id"], "t_user", ["id"], "CASCADE"),
        ("fk_appointment_doctor", "t_appointment", ["doctor_id"], "t_doctor", ["id"], "RESTRICT"),
        ("fk_appointment_department", "t_appointment", ["department_id"], "t_department", ["id"], "RESTRICT"),
        ("fk_record_user", "t_health_record", ["user_id"], "t_user", ["id"], "CASCADE"),
        ("fk_record_doctor", "t_health_record", ["doctor_id"], "t_doctor", ["id"], "SET NULL"),
    ]
    for args in foreign_keys:
        _add_fk(*args)

    _add_check("ck_appointment_status", "t_appointment", "status IN (0, 1, 2, 3, 4)")
    _add_check("ck_doctor_consult_status", "t_doctor_consult", "status IN (0, 1, 2, 3)")
    _add_check("ck_knowledge_vector_status", "t_knowledge_file", "vector_status IN (0, 1, 2, 3)")
    _add_check("ck_message_delivery_status", "t_consult_message", "delivery_status IN ('pending','completed','failed','cancelled')")


def downgrade() -> None:
    # 数据约束降级需人工评审，避免自动破坏生产一致性。
    pass
