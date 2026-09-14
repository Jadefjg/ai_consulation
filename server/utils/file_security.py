"""上传文件安全校验：文件名、扩展名、真实格式及压缩包风险。"""
import io
import os
import zipfile
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError


@dataclass
class UploadSecurityError(ValueError):
    message: str

    def __str__(self) -> str:
        return self.message


def validate_filename(filename: str) -> str:
    name = (filename or "").strip()
    if not name or len(name) > 255 or "\x00" in name:
        raise UploadSecurityError("文件名无效")
    if os.path.basename(name) != name or "/" in name or "\\" in name:
        raise UploadSecurityError("文件名不能包含路径")
    return name


def validate_knowledge_file(filename: str, content: bytes, content_type: str | None) -> str:
    name = validate_filename(filename)
    ext = os.path.splitext(name)[1].lower()
    allowed_mimes = {
        ".txt": {"text/plain", "application/octet-stream"},
        ".md": {"text/plain", "text/markdown", "application/octet-stream"},
        ".pdf": {"application/pdf", "application/octet-stream"},
        ".doc": {"application/msword", "application/octet-stream"},
        ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip", "application/octet-stream"},
    }
    if ext not in allowed_mimes:
        raise UploadSecurityError("不支持的文件类型，仅支持 txt/md/pdf/doc/docx")
    if content_type and content_type.lower().split(";", 1)[0] not in allowed_mimes[ext]:
        raise UploadSecurityError("文件声明类型与扩展名不匹配")
    if ext in {".txt", ".md"}:
        if b"\x00" in content:
            raise UploadSecurityError("文本文件包含非法二进制内容")
        try:
            content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise UploadSecurityError("文本文件必须使用 UTF-8 编码") from exc
    elif ext == ".pdf":
        if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-2048:]:
            raise UploadSecurityError("PDF 文件结构无效")
    elif ext == ".doc":
        if not content.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
            raise UploadSecurityError("DOC 文件结构无效")
    else:
        _validate_docx(content)
    return ext


def _validate_docx(content: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = set(archive.namelist())
            if not {"[Content_Types].xml", "word/document.xml"}.issubset(names):
                raise UploadSecurityError("DOCX 文件结构无效")
            total_uncompressed = sum(item.file_size for item in archive.infolist())
            if total_uncompressed > 100 * 1024 * 1024 or total_uncompressed > max(len(content) * 100, 1):
                raise UploadSecurityError("DOCX 解压后体积异常")
            if any(item.filename.startswith(("/", "\\")) or ".." in item.filename.split("/") for item in archive.infolist()):
                raise UploadSecurityError("DOCX 包含不安全路径")
    except zipfile.BadZipFile as exc:
        raise UploadSecurityError("DOCX 文件结构无效") from exc


def validate_avatar(filename: str, content: bytes) -> str:
    name = validate_filename(filename)
    ext = os.path.splitext(name)[1].lower()
    expected = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".gif": "GIF", ".webp": "WEBP"}
    if ext not in expected:
        raise UploadSecurityError("头像仅支持 jpg/png/gif/webp")
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
            if image.format != expected[ext]:
                raise UploadSecurityError("头像真实格式与扩展名不匹配")
    except (UnidentifiedImageError, OSError) as exc:
        raise UploadSecurityError("图片文件无效") from exc
    return ext
