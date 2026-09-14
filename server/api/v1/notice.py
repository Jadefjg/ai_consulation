"""系统公告接口"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.response import success, page_result
from db.session import get_db
from models.article import Notice
from schemas.common import NoticeCreate
from utils.helpers import format_datetime
from services.redis_service import cache_delete_pattern, cache_get, cache_set

router = APIRouter()


@router.get("/list")
def list_notices(db: Session = Depends(get_db)):
    """公告列表（公开，仅已发布）"""
    cached = cache_get("notices:list")
    if cached is not None:
        return cached
    items = db.query(Notice).filter(Notice.status == 1).order_by(Notice.id.desc()).all()
    data = [{"id": n.id, "title": n.title, "content": n.content, "create_time": format_datetime(n.create_time)} for n in items]
    result = success(data)
    cache_set("notices:list", result)
    return result


@router.get("/admin/list")
def admin_list_notices(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """公告管理列表（管理员，含全部状态）"""
    q = db.query(Notice)
    kw = keyword.strip()
    if kw:
        q = q.filter((Notice.title.like(f"%{kw}%")) | (Notice.content.like(f"%{kw}%")))
    total = q.count()
    items = q.order_by(Notice.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    data = [{
        "id": n.id,
        "title": n.title,
        "content": n.content,
        "status": n.status,
        "create_time": format_datetime(n.create_time),
        "update_time": format_datetime(n.update_time),
    } for n in items]
    return page_result(data, total, page, page_size)


@router.get("/{notice_id}")
def get_notice(notice_id: int, db: Session = Depends(get_db)):
    """公告详情"""
    notice = db.query(Notice).filter(Notice.id == notice_id, Notice.status == 1).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在或已下架")
    return success({
        "id": notice.id,
        "title": notice.title,
        "content": notice.content,
        "create_time": format_datetime(notice.create_time),
    })


@router.post("/create")
def create_notice(req: NoticeCreate, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    """创建公告"""
    notice = Notice(title=req.title, content=req.content, status=req.status)
    db.add(notice)
    db.commit()
    cache_delete_pattern("notices:*")
    return success({"id": notice.id}, "创建成功")


@router.put("/{notice_id}")
def update_notice(
    notice_id: int,
    req: NoticeCreate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """更新公告"""
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    notice.title = req.title
    notice.content = req.content
    notice.status = req.status
    db.commit()
    cache_delete_pattern("notices:*")
    return success(None, "更新成功")


@router.delete("/{notice_id}")
def delete_notice(notice_id: int, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    """删除公告"""
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    db.delete(notice)
    db.commit()
    cache_delete_pattern("notices:*")
    return success(None, "删除成功")
