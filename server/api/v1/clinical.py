"""P2 临床工作流：结构化采集、AI转人工、医生审核与病历归档。"""
import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.deps import CurrentUser, require_roles
from core.response import success
from db.session import get_db
from models.appointment import HealthRecord
from models.clinical import AIConsultReview, SymptomAssessment
from models.consult import ConsultMessage, ConsultSession
from models.doctor import Doctor
from models.doctor_consult import DoctorConsult
from models.operations import AuditLog, Notification
from schemas.common import AIReviewCreate, AITransferCreate, SymptomAssessmentCreate
from utils.helpers import format_datetime

router = APIRouter()


def _session_summary(db: Session, session_id: int) -> str:
    messages = db.query(ConsultMessage).filter(ConsultMessage.session_id == session_id).order_by(ConsultMessage.id).all()
    if not messages:
        raise HTTPException(status_code=400, detail="会话暂无可交接内容")
    lines = []
    for item in messages[-12:]:
        speaker = "患者" if item.role == "user" else "AI建议"
        lines.append(f"{speaker}：{item.content[:1000]}")
    return "\n".join(lines)[:8000]


@router.post("/symptoms")
def create_symptom_assessment(req: SymptomAssessmentCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    if req.session_id and not db.query(ConsultSession).filter(ConsultSession.id == req.session_id, ConsultSession.user_id == current.user_id).first():
        raise HTTPException(status_code=404, detail="AI会话不存在")
    symptoms = list(dict.fromkeys(s.strip() for s in req.symptoms if s.strip()))
    if not symptoms:
        raise HTTPException(status_code=400, detail="请至少填写一个症状")
    row = SymptomAssessment(user_id=current.user_id, session_id=req.session_id, symptoms_json=json.dumps(symptoms, ensure_ascii=False), onset_time=req.onset_time, duration=req.duration, severity=req.severity, temperature=req.temperature, extra_json=json.dumps(req.extra, ensure_ascii=False) if req.extra is not None else None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return success({"id": row.id, "symptoms": symptoms}, "症状信息已保存")


@router.post("/transfer")
def transfer_ai_to_doctor(req: AITransferCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    session = db.query(ConsultSession).filter(ConsultSession.id == req.session_id, ConsultSession.user_id == current.user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="AI会话不存在")
    if req.doctor_id and not db.query(Doctor).filter(Doctor.id == req.doctor_id, Doctor.status == 1).first():
        raise HTTPException(status_code=400, detail="医生不存在或已停用")
    existing = db.query(AIConsultReview).filter(AIConsultReview.session_id == session.id).first()
    if existing:
        return success({"consult_id": existing.consult_id, "review_id": existing.id}, "该会话已转人工")
    summary = _session_summary(db, session.id)
    consult = DoctorConsult(user_id=current.user_id, doctor_id=req.doctor_id, chief_complaint=f"AI转人工：{session.title}", status=0)
    db.add(consult)
    db.flush()
    review = AIConsultReview(session_id=session.id, consult_id=consult.id, user_id=current.user_id, doctor_id=req.doctor_id, ai_summary=summary)
    db.add(review)
    db.commit()
    db.refresh(review)
    return success({"consult_id": consult.id, "review_id": review.id}, "已转人工问诊")


@router.get("/my-reviews")
def my_ai_reviews(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """患者查看 AI 问诊的医生审核结果，补齐转人工后的反馈闭环。"""
    rows = db.query(AIConsultReview).filter(
        AIConsultReview.user_id == current.user_id
    ).order_by(AIConsultReview.id.desc()).all()
    return success([{
        "id": row.id,
        "session_id": row.session_id,
        "review_status": row.review_status,
        "status_text": {0: "待医生审核", 1: "已审核通过", 2: "医生已修订"}.get(row.review_status, "未知"),
        "doctor_comment": row.doctor_comment,
        "record_id": row.record_id,
        "review_time": format_datetime(row.review_time),
    } for row in rows])


@router.get("/doctor/reviews")
def doctor_reviews(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("doctor"))):
    rows = db.query(AIConsultReview).join(DoctorConsult, DoctorConsult.id == AIConsultReview.consult_id).filter(DoctorConsult.doctor_id == current.user_id).order_by(AIConsultReview.id.desc()).all()
    return success([{"id": r.id, "consult_id": r.consult_id, "user_id": r.user_id, "ai_summary": r.ai_summary, "review_status": r.review_status, "doctor_comment": r.doctor_comment, "record_id": r.record_id, "create_time": format_datetime(r.create_time)} for r in rows])


@router.put("/doctor/reviews/{review_id}")
def review_ai_advice(review_id: int, req: AIReviewCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("doctor"))):
    row = db.query(AIConsultReview).join(DoctorConsult, DoctorConsult.id == AIConsultReview.consult_id).filter(AIConsultReview.id == review_id, DoctorConsult.doctor_id == current.user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="待审核记录不存在或无权限")
    comment = (req.doctor_comment or "").strip()
    if not req.approved and not comment:
        raise HTTPException(status_code=400, detail="修订 AI 建议时必须填写医生意见")
    row.doctor_id = current.user_id
    row.review_status = 1 if req.approved else 2
    row.doctor_comment = comment
    row.review_time = datetime.now()
    if req.archive_record and not row.record_id:
        record = HealthRecord(user_id=row.user_id, doctor_id=current.user_id, record_type="AI问诊审核摘要", diagnosis="AI建议经医生审核" if req.approved else "AI建议经医生修订", treatment=comment or row.ai_summary, visit_date=date.today())
        db.add(record)
        db.flush()
        row.record_id = record.id
    db.add(Notification(user_id=row.user_id, title="AI问诊建议已由医生审核", content="医生已完成审核，请查看人工咨询或健康档案。", type="ai_review"))
    db.add(AuditLog(actor_id=current.user_id, actor_role=current.role, action="review_ai_consult", target_type="ai_review", target_id=row.id, detail=f"status={row.review_status}, archive={req.archive_record}"))
    db.commit()
    return success({"record_id": row.record_id}, "审核完成")
