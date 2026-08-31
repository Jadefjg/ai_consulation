"""确保 root 超级管理员账号存在"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from models.admin import Admin
from core.security import hash_password

ROOT_USERNAME = "admin"
ROOT_PASSWORD = "feng1010"
ROOT_NICKNAME = "超级管理员"


def ensure_root_admin() -> None:
    """创建或更新 root 超级管理员（admin / feng1010）"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.username == ROOT_USERNAME).first()
        hashed = hash_password(ROOT_PASSWORD)
        if admin:
            admin.password = hashed
            admin.admin_role = "root"
            admin.nickname = ROOT_NICKNAME
            admin.status = 1
            from datetime import datetime
            admin.update_time = datetime.now()
            print(f"[root] 已更新超级管理员: {ROOT_USERNAME}")
        else:
            db.add(Admin(
                username=ROOT_USERNAME,
                password=hashed,
                nickname=ROOT_NICKNAME,
                admin_role="root",
                status=1,
            ))
            print(f"[root] 已创建超级管理员: {ROOT_USERNAME}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    ensure_root_admin()
