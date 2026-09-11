"""知识库管理接口"""
import os
import hashlib
from fastapi import APIRouter, Depends, UploadFile, File, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.deps import require_roles, CurrentUser
from core.response import success, page_result
from db.session import get_db
from models.knowledge import KnowledgeFile, KnowledgeChunk
from models.p3 import KnowledgeVersion
from services.rag_service import get_rag_service
from utils.helpers import save_upload_file, get_file_type, format_datetime

router = APIRouter()

_KNOWLEDGE_MAX_BYTES = 20 * 1024 * 1024


def _vectorize_task(file_id: int):
    """后台向量化任务"""
    from db.session import SessionLocal
    db = SessionLocal()
    try:
        file_record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
        if file_record:
            try:
                chunk_count = get_rag_service().process_file(db, file_record)
                print(f"[knowledge] 向量化成功 file_id={file_id}, chunks={chunk_count}", flush=True)
            except Exception as exc:
                print(f"[knowledge] 向量化失败 file_id={file_id}, file={file_record.file_name}: {exc}", flush=True)
    finally:
        db.close()


@router.get("/list")
def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """知识库文件列表（支持按文件名、类型搜索）"""
    q = db.query(KnowledgeFile)
    kw = keyword.strip()
    if kw:
        q = q.filter(
            (KnowledgeFile.file_name.like(f"%{kw}%"))
            | (KnowledgeFile.file_type.like(f"%{kw}%"))
        )
    total = q.count()
    items = q.order_by(KnowledgeFile.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    data = [{
        "id": f.id, "file_name": f.file_name, "file_type": f.file_type,
        "file_size": f.file_size, "chunk_count": f.chunk_count,
        "vector_status": f.vector_status,
        "create_time": format_datetime(f.create_time),
    } for f in items]
    return page_result(data, total, page, page_size)


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_roles("admin")),
):
    """上传知识库文件并自动向量化"""
    file_type = get_file_type(file.filename)
    if file_type == "unknown":
        raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持 txt/doc/pdf/markdown")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(content) > _KNOWLEDGE_MAX_BYTES:
        raise HTTPException(status_code=400, detail="文件大小不能超过20MB")
    rel_path = save_upload_file(content, file.filename, "knowledge")
    abs_path = os.path.join(settings.upload_dir, "knowledge", os.path.basename(rel_path))
    record = KnowledgeFile(
        file_name=file.filename,
        file_type=file_type,
        file_size=len(content),
        file_path=abs_path.replace("\\", "/"),
        upload_by=current.user_id,
        upload_role=current.role,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    version = KnowledgeVersion(file_id=record.id, version=1, content_hash=hashlib.sha256(content).hexdigest(), status=0)
    db.add(version)
    db.commit()
    return success({"id": record.id, "version_id": version.id, "file_name": record.file_name}, "上传成功，等待审核")


@router.put("/versions/{version_id}/review")
def review_version(version_id: int, approved: bool, background_tasks: BackgroundTasks, comment: str = "", db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("admin"))):
    version = db.query(KnowledgeVersion).filter(KnowledgeVersion.id == version_id).first()
    if not version: raise HTTPException(status_code=404, detail="知识版本不存在")
    if version.status != 0: raise HTTPException(status_code=409, detail="该版本已审核")
    version.status = 1 if approved else 2
    version.reviewer_id = current.user_id
    version.review_comment = comment.strip()
    db.commit()
    if approved: background_tasks.add_task(_vectorize_task, version.file_id)
    return success(None, "审核通过，正在发布" if approved else "版本已驳回")


@router.get("/versions")
def list_versions(db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    rows = db.query(KnowledgeVersion).order_by(KnowledgeVersion.id.desc()).all()
    return success([{"id": r.id, "file_id": r.file_id, "version": r.version, "status": r.status, "reviewer_id": r.reviewer_id, "review_comment": r.review_comment, "create_time": format_datetime(r.create_time)} for r in rows])


@router.post("/{file_id}/revectorize")
def revectorize(file_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    """重新向量化"""
    record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")
    background_tasks.add_task(_vectorize_task, file_id)
    return success(None, "已开始重新向量化")


@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    """删除知识库文件"""
    record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")
    get_rag_service().vector_store.delete_by_file_id(file_id)
    db.query(KnowledgeChunk).filter(KnowledgeChunk.file_id == file_id).delete()
    if os.path.exists(record.file_path):
        os.remove(record.file_path)
    db.delete(record)
    db.commit()
    return success(None, "删除成功")
