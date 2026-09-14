"""健康科普文章接口"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, update
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.response import success, page_result
from db.session import get_db
from models.article import Article
from schemas.common import ArticleCreate
from utils.helpers import format_datetime
from services.redis_service import cache_delete_pattern, cache_get, cache_set

router = APIRouter()


@router.get("/list")
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: str = "",
    db: Session = Depends(get_db),
):
    """文章列表（公开，仅已发布）"""
    cache_key = f"articles:list:{page}:{page_size}:{category}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    q = db.query(Article).filter(Article.status == 1)
    if category:
        q = q.filter(Article.category == category)
    total = q.count()
    items = q.order_by(Article.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    data = [{
        "id": a.id, "title": a.title, "category": a.category, "cover": a.cover,
        "summary": a.summary, "view_count": a.view_count,
        "create_time": format_datetime(a.create_time),
    } for a in items]
    result = page_result(data, total, page, page_size)
    cache_set(cache_key, result)
    return result


@router.get("/admin/list")
def admin_list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """文章管理列表（管理员，含全部状态）"""
    q = db.query(Article)
    kw = keyword.strip()
    if kw:
        q = q.filter(
            (Article.title.like(f"%{kw}%"))
            | (Article.summary.like(f"%{kw}%"))
            | (Article.category.like(f"%{kw}%"))
        )
    total = q.count()
    items = q.order_by(Article.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    data = [{
        "id": a.id, "title": a.title, "category": a.category, "cover": a.cover,
        "summary": a.summary, "view_count": a.view_count, "status": a.status,
        "create_time": format_datetime(a.create_time),
    } for a in items]
    return page_result(data, total, page, page_size)


@router.get("/admin/{article_id}")
def admin_get_article(
    article_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """文章详情（管理员，不计浏览量）"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return success({
        "id": article.id,
        "title": article.title,
        "category": article.category,
        "summary": article.summary,
        "content": article.content,
        "status": article.status,
        "view_count": article.view_count,
        "create_time": format_datetime(article.create_time),
    })


@router.get("/{article_id}")
def get_article(article_id: int, db: Session = Depends(get_db)):
    """文章详情（公开，仅已发布）"""
    article = db.query(Article).filter(Article.id == article_id, Article.status == 1).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在或已下架")
    db.execute(
        update(Article)
        .where(Article.id == article_id, Article.status == 1)
        .values(view_count=func.coalesce(Article.view_count, 0) + 1)
    )
    db.commit()
    db.refresh(article)
    return success({
        "id": article.id,
        "title": article.title,
        "category": article.category,
        "content": article.content,
        "view_count": article.view_count,
        "create_time": format_datetime(article.create_time),
    })


@router.post("/create")
def create_article(req: ArticleCreate, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    """创建文章"""
    article = Article(title=req.title, category=req.category, summary=req.summary, content=req.content, status=req.status)
    db.add(article)
    db.commit()
    cache_delete_pattern("articles:list:*")
    return success({"id": article.id}, "创建成功")


@router.put("/{article_id}")
def update_article(article_id: int, req: ArticleCreate, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    """更新文章"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    article.title = req.title
    article.category = req.category
    article.summary = req.summary
    article.content = req.content
    article.status = req.status
    db.commit()
    cache_delete_pattern("articles:list:*")
    return success(None, "更新成功")


@router.delete("/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    """删除文章"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    db.delete(article)
    db.commit()
    cache_delete_pattern("articles:list:*")
    return success(None, "删除成功")
