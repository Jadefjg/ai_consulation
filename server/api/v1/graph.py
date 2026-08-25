"""知识图谱接口"""
from fastapi import APIRouter, Depends
from core.deps import require_roles, CurrentUser
from core.response import success
from schemas.common import GraphQueryRequest
from services.graph_service import get_graph_service

router = APIRouter()


@router.post("/infer")
def infer_diseases(req: GraphQueryRequest, _: CurrentUser = Depends(require_roles("user", "admin", "doctor"))):
    """根据症状推理可能疾病"""
    results = get_graph_service().infer_diseases_by_symptoms(req.symptoms)
    return success(results)


@router.get("/disease/{name}")
def disease_detail(name: str):
    """获取疾病详情"""
    detail = get_graph_service().get_disease_detail(name)
    return success(detail)


@router.get("/full")
def full_graph():
    """获取完整知识图谱（默认可视化）"""
    graph = get_graph_service().get_full_graph()
    return success(graph)


@router.get("/subgraph")
def entity_subgraph(entity: str):
    """获取实体子图（可视化）"""
    graph = get_graph_service().get_entity_subgraph(entity)
    return success(graph)


@router.get("/search")
def search_entities(keyword: str):
    """搜索图谱实体"""
    results = get_graph_service().search_entities(keyword)
    return success(results)


@router.get("/stats")
def graph_stats(_: CurrentUser = Depends(require_roles("admin"))):
    """图谱统计"""
    stats = get_graph_service().get_graph_stats()
    return success(stats)
