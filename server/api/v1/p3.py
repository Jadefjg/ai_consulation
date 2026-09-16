"""P3 随访、慢病与风险管理接口。"""
import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.deps import CurrentUser, require_roles
from core.response import success
from db.session import get_db
from models.appointment import Appointment
from models.doctor import Doctor
from models.doctor_consult import DoctorConsult
from models.p3 import ChronicMetric, ChronicRecord, FollowupPlan, FollowupTask, RiskAssessment
from schemas.common import ChronicCreate, FollowupPlanCreate, FollowupResponse, MetricCreate, RiskAssessmentCreate
from utils.helpers import format_datetime

router = APIRouter()


def _doctor_name_map(db: Session, doctor_ids: set[int]) -> dict[int, str]:
    if not doctor_ids:
        return {}
    return {
        row.id: row.real_name or row.username
        for row in db.query(Doctor).filter(Doctor.id.in_(doctor_ids)).all()
    }


@router.post("/followups")
def create_followup(req: FollowupPlanCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("doctor"))):
    related = db.query(Appointment.id).filter(Appointment.user_id == req.user_id, Appointment.doctor_id == current.user_id).first() or db.query(DoctorConsult.id).filter(DoctorConsult.user_id == req.user_id, DoctorConsult.doctor_id == current.user_id).first()
    if not related:
        raise HTTPException(status_code=403, detail="只能为有预约或问诊关系的患者创建随访")
    plan = FollowupPlan(user_id=req.user_id, doctor_id=current.user_id, title=req.title, frequency_days=req.frequency_days, next_date=req.next_date, notes=req.notes)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    db.add(FollowupTask(plan_id=plan.id, due_date=plan.next_date))
    db.commit()
    return success({"id": plan.id}, "随访计划已创建")


@router.get("/followups")
def list_followups(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user", "doctor"))):
    q = db.query(FollowupPlan).filter(FollowupPlan.user_id == current.user_id) if current.role == "user" else db.query(FollowupPlan).filter(FollowupPlan.doctor_id == current.user_id)
    plans = q.order_by(FollowupPlan.id.desc()).all()
    names = _doctor_name_map(db, {p.doctor_id for p in plans if p.doctor_id})
    items = []
    for p in plans:
        task = db.query(FollowupTask).filter(FollowupTask.plan_id == p.id, FollowupTask.status == 0).order_by(FollowupTask.due_date).first()
        items.append({
            "id": p.id,
            "task_id": task.id if task else None,
            "user_id": p.user_id,
            "doctor_id": p.doctor_id,
            "doctor_name": names.get(p.doctor_id, ""),
            "title": p.title,
            "frequency_days": p.frequency_days,
            "next_date": str(p.next_date),
            "due_date": str(task.due_date) if task else None,
            "status": p.status,
            "notes": p.notes,
            "can_complete": bool(task),
        })
    return success(items)


@router.post("/followups/{task_id}/complete")
def complete_followup(task_id: int, req: FollowupResponse, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    task = db.query(FollowupTask).join(FollowupPlan, FollowupPlan.id == FollowupTask.plan_id).filter(
        FollowupTask.id == task_id,
        FollowupPlan.user_id == current.user_id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="随访任务不存在")
    if task.status != 0:
        raise HTTPException(status_code=400, detail="该随访任务已完成")
    task.response = req.response.strip()
    task.status = 1
    task.completed_time = datetime.now()
    plan = db.query(FollowupPlan).filter(FollowupPlan.id == task.plan_id).first()
    next_date = None
    if plan and plan.status == 1:
        next_date = (task.due_date or date.today()) + timedelta(days=plan.frequency_days or 30)
        plan.next_date = next_date
        db.add(FollowupTask(plan_id=plan.id, due_date=next_date, status=0))
    db.commit()
    return success({"next_date": str(next_date) if next_date else None}, "随访已完成")


@router.post("/chronic")
def create_chronic(req: ChronicCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    row = ChronicRecord(user_id=current.user_id, disease=req.disease.strip(), target_json=json.dumps(req.target, ensure_ascii=False) if req.target is not None else None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return success({"id": row.id}, "慢病档案已创建")


@router.get("/chronic")
def list_chronic(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """获取当前用户自己的慢病档案，供指标记录选择。"""
    rows = db.query(ChronicRecord).filter(
        ChronicRecord.user_id == current.user_id,
        ChronicRecord.status == 1,
    ).order_by(ChronicRecord.id.desc()).all()
    data = []
    for row in rows:
        metrics = db.query(ChronicMetric).filter(ChronicMetric.chronic_id == row.id).order_by(ChronicMetric.id.desc()).limit(5).all()
        data.append({
            "id": row.id,
            "disease": row.disease,
            "status": row.status,
            "recent_metrics": [
                {"id": item.id, "metric": item.metric, "value": item.value, "measured_at": format_datetime(item.measured_at)}
                for item in metrics
            ],
        })
    return success(data)


@router.get("/chronic/{chronic_id}/metrics")
def list_metrics(chronic_id: int, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    row = db.query(ChronicRecord).filter(ChronicRecord.id == chronic_id, ChronicRecord.user_id == current.user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="未找到属于当前用户的慢病档案")
    items = db.query(ChronicMetric).filter(ChronicMetric.chronic_id == chronic_id).order_by(ChronicMetric.id.desc()).limit(50).all()
    return success([
        {"id": item.id, "metric": item.metric, "value": item.value, "measured_at": format_datetime(item.measured_at)}
        for item in items
    ])


@router.post("/chronic/{chronic_id}/metrics")
def add_metric(chronic_id: int, req: MetricCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    row = db.query(ChronicRecord).filter(ChronicRecord.id == chronic_id, ChronicRecord.user_id == current.user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="未找到属于当前用户的慢病档案，请先创建或选择正确的档案")
    db.add(ChronicMetric(chronic_id=chronic_id, metric=req.metric.strip(), value=req.value.strip()))
    db.commit()
    return success(None, "指标已记录")


@router.post("/risk/assess")
def assess_risk(req: RiskAssessmentCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    factors = req.factors or {}
    score = 0
    if factors.get("age", 0) >= 65:
        score += 2
    if factors.get("chronic_count", 0) >= 2:
        score += 2
    if factors.get("emergency_symptom"):
        score += 5
    if factors.get("severe", False):
        score += 3
    level = "高风险" if score >= 5 else ("中风险" if score >= 3 else "低风险")
    row = RiskAssessment(user_id=current.user_id, score=score, level=level, factors_json=json.dumps(factors, ensure_ascii=False))
    db.add(row)
    db.commit()
    db.refresh(row)
    advice = "请尽快就医" if score >= 5 else "建议持续观察并按计划随访"
    return success({"id": row.id, "score": score, "level": level, "advice": advice})
