"""工具函数模块"""
from datetime import datetime, date
from typing import Optional
import os
import uuid


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """格式化日期时间为 2026-11-02 17:25:17"""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_date(d: Optional[date]) -> Optional[str]:
    """格式化日期为 2026-11-02"""
    if not d:
        return None
    return d.strftime("%Y-%m-%d")


def save_upload_file(file_content: bytes, original_name: str, sub_dir: str = "") -> str:
    """
    保存上传文件到 D:/uploads33
    :return: 相对路径 /uploads33/sub_dir/filename
    """
    from core.config import settings
    upload_base = settings.upload_dir
    target_dir = os.path.join(upload_base, sub_dir) if sub_dir else upload_base
    os.makedirs(target_dir, exist_ok=True)
    ext = os.path.splitext(original_name)[1]
    new_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(target_dir, new_name)
    with open(file_path, "wb") as f:
        f.write(file_content)
    rel_path = f"/uploads33/{sub_dir}/{new_name}" if sub_dir else f"/uploads33/{new_name}"
    return rel_path.replace("\\", "/")


def get_file_type(filename: str) -> str:
    """根据扩展名获取文件类型"""
    ext = os.path.splitext(filename)[1].lower()
    mapping = {".txt": "txt", ".md": "markdown", ".pdf": "pdf", ".doc": "doc", ".docx": "docx"}
    return mapping.get(ext, "unknown")
