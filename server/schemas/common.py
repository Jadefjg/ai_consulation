"""Pydantic请求/响应模型"""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ========== 通用 ==========
class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    role: str = Field(..., description="角色: user/doctor/admin")


class RegisterRequest(BaseModel):
    """患者注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    real_name: Optional[str] = None
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


class ProfileUpdateRequest(BaseModel):
    """个人资料更新"""
    nickname: Optional[str] = None
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None
    allergy_history: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    introduction: Optional[str] = None


# ========== 用户/医生/科室 ==========
class UserOut(BaseModel):
    """用户输出"""
    id: int
    username: str
    real_name: Optional[str] = None
    gender: Optional[int] = 1
    age: Optional[int] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    allergy_history: Optional[str] = None
    status: int = 1
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """管理员创建用户"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    confirm_password: str = Field(..., min_length=6, description="确认密码")
    real_name: Optional[str] = None
    gender: int = 1
    age: Optional[int] = None
    phone: Optional[str] = None
    allergy_history: Optional[str] = None
    status: int = 1


class UserUpdate(BaseModel):
    """管理员更新用户"""
    real_name: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    allergy_history: Optional[str] = None
    status: Optional[int] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None


class DoctorOut(BaseModel):
    """医生输出"""
    id: int
    username: str
    real_name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    introduction: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    status: int = 1
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class DoctorCreate(BaseModel):
    """管理员创建医生"""
    username: str = Field(..., min_length=3, max_length=50, description="登录账号")
    password: str = Field(..., min_length=6, description="密码")
    confirm_password: str = Field(..., min_length=6, description="确认密码")
    real_name: str = Field(..., min_length=1, max_length=50, description="医生姓名")
    department_id: Optional[int] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    introduction: Optional[str] = None
    phone: Optional[str] = None
    status: int = 1


class DoctorUpdate(BaseModel):
    """管理员更新医生"""
    real_name: Optional[str] = None
    department_id: Optional[int] = None
    title: Optional[str] = None
    specialty: Optional[str] = None
    introduction: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[int] = None
    password: Optional[str] = None
    confirm_password: Optional[str] = None


class DepartmentOut(BaseModel):
    """科室输出"""
    id: int
    name: str
    description: Optional[str] = None
    sort_order: int = 0
    status: int = 1
    doctor_count: int = 0
    create_time: Optional[str] = None

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    """科室创建"""
    name: str
    description: Optional[str] = None
    sort_order: int = 0


# ========== 知识库 ==========
class KnowledgeFileOut(BaseModel):
    """知识库文件输出"""
    id: int
    file_name: str
    file_type: str
    file_size: int = 0
    chunk_count: int = 0
    vector_status: int = 0
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== AI问诊 ==========
class ChatRequest(BaseModel):
    """AI问诊请求"""
    session_id: Optional[int] = None
    message: str = Field(..., min_length=1)


class SessionOut(BaseModel):
    """会话输出"""
    id: int
    title: str
    message_count: int = 0
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    """消息输出"""
    id: int
    session_id: int
    role: str
    content: str
    references_json: Optional[str] = None
    graph_json: Optional[str] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 人工问诊 ==========
class DoctorConsultCreate(BaseModel):
    """创建人工问诊"""
    doctor_id: Optional[int] = None
    chief_complaint: str


class DoctorReplyCreate(BaseModel):
    """医生回复"""
    consult_id: int
    content: str


class DoctorConsultOut(BaseModel):
    """人工问诊输出"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    chief_complaint: str
    status: int = 0
    create_time: Optional[datetime] = None
    replies: Optional[List[Any]] = None


# ========== 预约 ==========
class AppointmentCreate(BaseModel):
    """创建预约"""
    doctor_id: int
    department_id: int
    visit_date: date
    time_slot: str
    remark: Optional[str] = None


class AppointmentOut(BaseModel):
    """预约输出"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    doctor_id: int
    doctor_name: Optional[str] = None
    department_id: int
    department_name: Optional[str] = None
    visit_date: date
    time_slot: str
    status: int = 0
    remark: Optional[str] = None
    create_time: Optional[datetime] = None


# ========== 健康档案 ==========
class HealthRecordCreate(BaseModel):
    """创建健康档案"""
    user_id: int
    record_type: str
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    prescription: Optional[str] = None
    visit_date: Optional[date] = None


class HealthRecordUpdate(BaseModel):
    """更新健康档案"""
    record_type: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    prescription: Optional[str] = None
    visit_date: Optional[date] = None


class HealthRecordOut(BaseModel):
    """健康档案输出"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    record_type: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    prescription: Optional[str] = None
    visit_date: Optional[date] = None
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== 文章/公告 ==========
class ArticleOut(BaseModel):
    """文章输出"""
    id: int
    title: str
    category: Optional[str] = None
    cover: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    view_count: int = 0
    status: int = 1
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArticleCreate(BaseModel):
    """文章创建"""
    title: str
    category: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    status: int = 1


class NoticeOut(BaseModel):
    """公告输出"""
    id: int
    title: str
    content: Optional[str] = None
    status: int = 1
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class NoticeCreate(BaseModel):
    """公告创建/更新"""
    title: str
    content: str = ""
    status: int = 1


# ========== 图谱 ==========
class GraphQueryRequest(BaseModel):
    """图谱查询请求"""
    symptoms: List[str] = Field(default_factory=list)
    disease: Optional[str] = None
    entity: Optional[str] = None


# ========== 统计 ==========
class StatOverview(BaseModel):
    """统计概览"""
    user_count: int = 0
    doctor_count: int = 0
    consult_count: int = 0
    appointment_count: int = 0
    knowledge_count: int = 0
    article_count: int = 0
