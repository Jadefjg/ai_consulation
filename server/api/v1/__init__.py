"""API v1 路由汇总"""
from fastapi import APIRouter
from api.v1 import auth, user, doctor, department, knowledge, chat, graph, consult, appointment, record, article, notice, stat, profile

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(user.router, prefix="/users", tags=["用户管理"])
api_router.include_router(doctor.router, prefix="/doctors", tags=["医生管理"])
api_router.include_router(department.router, prefix="/departments", tags=["科室管理"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI问诊"])
api_router.include_router(graph.router, prefix="/graph", tags=["知识图谱"])
api_router.include_router(consult.router, prefix="/consult", tags=["人工问诊"])
api_router.include_router(appointment.router, prefix="/appointments", tags=["预约挂号"])
api_router.include_router(record.router, prefix="/records", tags=["健康档案"])
api_router.include_router(article.router, prefix="/articles", tags=["健康科普"])
api_router.include_router(notice.router, prefix="/notices", tags=["系统公告"])
api_router.include_router(stat.router, prefix="/stat", tags=["数据统计"])
api_router.include_router(profile.router, prefix="/profile", tags=["个人中心"])
