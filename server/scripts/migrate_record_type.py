"""健康档案 record_type 字段迁移脚本"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pymysql
from core.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE


def main():
    """执行 record_type 字段迁移"""
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
    )
    cur = conn.cursor()
    cur.execute("SHOW COLUMNS FROM t_health_record LIKE 'record_type'")
    if not cur.fetchone():
        cur.execute(
            "ALTER TABLE t_health_record "
            "ADD COLUMN record_type VARCHAR(50) DEFAULT NULL COMMENT '档案类型' AFTER doctor_id"
        )
        cur.execute(
            "UPDATE t_health_record SET record_type = '门诊记录' "
            "WHERE record_type IS NULL OR record_type = ''"
        )
        conn.commit()
        print("Migration applied: record_type column added")
    else:
        print("Column record_type already exists")
    cur.execute(
        "SELECT id, user_id, record_type, diagnosis, create_time FROM t_health_record LIMIT 3"
    )
    for row in cur.fetchall():
        print(row)
    conn.close()


if __name__ == "__main__":
    main()
