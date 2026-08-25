"""ORM模型统一导出"""
from models.admin import Admin
from models.user import User
from models.department import Department
from models.doctor import Doctor
from models.knowledge import KnowledgeFile, KnowledgeChunk
from models.consult import ConsultSession, ConsultMessage
from models.doctor_consult import DoctorConsult, DoctorReply
from models.appointment import Appointment, HealthRecord
from models.article import Article, Notice

__all__ = [
    "Admin", "User", "Department", "Doctor",
    "KnowledgeFile", "KnowledgeChunk",
    "ConsultSession", "ConsultMessage",
    "DoctorConsult", "DoctorReply",
    "Appointment", "HealthRecord",
    "Article", "Notice",
]
