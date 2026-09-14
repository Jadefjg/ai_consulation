"""按显式环境变量初始化 root 超级管理员账号。"""
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from models.admin import Admin
from core.security import hash_password

logger = logging.getLogger(__name__)


def ensure_root_admin() -> bool:
    """仅在提供 ROOT_ADMIN_PASSWORD 时创建或更新超级管理员。"""
    password = os.getenv("ROOT_ADMIN_PASSWORD", "")
    if not password:
        logger.info("root bootstrap skipped", extra={"event": "root_bootstrap_skipped"})
        return False
    if len(password) < 12:
        raise RuntimeError("ROOT_ADMIN_PASSWORD 长度至少需要 12 个字符")
    username = os.getenv("ROOT_ADMIN_USERNAME", "admin")
    nickname = os.getenv("ROOT_ADMIN_NICKNAME", "超级管理员")
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.username == username).first()
        hashed = hash_password(password)
        if admin:
            admin.password = hashed
            admin.admin_role = "root"
            admin.nickname = nickname
            admin.status = 1
            from datetime import datetime
            admin.update_time = datetime.now()
            logger.info("root administrator updated", extra={"event": "root_updated"})
        else:
            db.add(Admin(
                username=username,
                password=hashed,
                nickname=nickname,
                admin_role="root",
                status=1,
            ))
            logger.info("root administrator created", extra={"event": "root_created"})
        db.commit()
        return True
    finally:
        db.close()


if __name__ == "__main__":
    ensure_root_admin()
