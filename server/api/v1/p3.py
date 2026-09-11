"""P3 随访、慢病与风险管理接口。"""
import json
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.deps import CurrentUser, require_roles
from core.response import success
from db.session import get_db
from models.p3 import FollowupPlan, FollowupTask, ChronicRecord, ChronicMetric, RiskAssessment
from models.appointment import Appointment
from models.doctor_consult import DoctorConsult
from schemas.common import FollowupPlanCreate, FollowupResponse, ChronicCreate, MetricCreate, RiskAssessmentCreate

router = APIRouter()

@router.post("/followups")
def create_followup(req: FollowupPlanCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("doctor"))):
    related = db.query(Appointment.id).filter(Appointment.user_id == req.user_id, Appointment.doctor_id == current.user_id).first() or db.query(DoctorConsult.id).filter(DoctorConsult.user_id == req.user_id, DoctorConsult.doctor_id == current.user_id).first()
    if not related: raise HTTPException(status_code=403, detail="只能为有预约或问诊关系的患者创建随访")
    plan = FollowupPlan(user_id=req.user_id, doctor_id=current.user_id, title=req.title, frequency_days=req.frequency_days, next_date=req.next_date, notes=req.notes)
    db.add(plan); db.commit(); db.refresh(plan)
    db.add(FollowupTask(plan_id=plan.id, due_date=plan.next_date)); db.commit()
    return success({"id": plan.id}, "随访计划已创建")

@router.get("/followups")
def list_followups(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user", "doctor"))):
    q = db.query(FollowupPlan).filter(FollowupPlan.user_id == current.user_id) if current.role == "user" else db.query(FollowupPlan).filter(FollowupPlan.doctor_id == current.user_id)
    items = []
    for p in q.order_by(FollowupPlan.id.desc()).all():
        task = db.query(FollowupTask).filter(FollowupTask.plan_id == p.id, FollowupTask.status == 0).order_by(FollowupTask.due_date).first()
        items.append({"id": p.id, "task_id": task.id if task else None, "user_id": p.user_id, "doctor_id": p.doctor_id, "title": p.title, "frequency_days": p.frequency_days, "next_date": str(p.next_date), "status": p.status, "notes": p.notes})
    return success(items)

@router.post("/followups/{task_id}/complete")
def complete_followup(task_id: int, req: FollowupResponse, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    task = db.query(FollowupTask).join(FollowupPlan, FollowupPlan.id == FollowupTask.plan_id).filter(FollowupTask.id == task_id, FollowupPlan.user_id == current.user_id).first()
    if not task: raise HTTPException(status_code=404, detail="随访任务不存在")
    task.response = req.response.strip(); task.status = 1; task.completed_time = datetime.now(); db.commit()
    return success(None, "随访已完成")

@router.post("/chronic")
def create_chronic(req: ChronicCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    row = ChronicRecord(user_id=current.user_id, disease=req.disease.strip(), target_json=json.dumps(req.target, ensure_ascii=False) if req.target is not None else None)
    db.add(row); db.commit(); db.refresh(row); return success({"id": row.id}, "慢病档案已创建")

@router.post("/chronic/{chronic_id}/metrics")
def add_metric(chronic_id: int, req: MetricCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    row = db.query(ChronicRecord).filter(ChronicRecord.id == chronic_id, ChronicRecord.user_id == current.user_id).first()
    if not row: raise HTTPException(status_code=404, detail="慢病档案不存在")
    db.add(ChronicMetric(chronic_id=chronic_id, metric=req.metric.strip(), value=req.value.strip())); db.commit(); return success(None, "指标已记录")

@router.post("/risk/assess")
def assess_risk(req: RiskAssessmentCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    factors = req.factors or {}; score = 0
    if factors.get("age", 0) >= 65: score += 2
    if factors.get("chronic_count", 0) >= 2: score += 2
    if factors.get("emergency_symptom"): score += 5
    if factors.get("severe", False): score += 3
    level = "高风险" if score >= 5 else ("中风险" if score >= 3 else "低风险")
    row = RiskAssessment(user_id=current.user_id, score=score, level=level, factors_json=json.dumps(factors, ensure_ascii=False)); db.add(row); db.commit(); db.refresh(row)
    return success({"id": row.id, "score": score, "level": level, "advice": "请尽快就医" if score >= 5 else "建议持续观察并按计划随访"})
