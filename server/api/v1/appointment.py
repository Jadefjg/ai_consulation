"""预约挂号接口"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.deps import require_roles, CurrentUser
from core.response import success, page_result
from db.session import get_db
from models.appointment import Appointment
from models.user import User
from models.doctor import Doctor
from models.department import Department
from models.operations import DoctorSchedule, Notification, AuditLog
from schemas.common import AppointmentCreate
from utils.helpers import format_datetime, format_date

router = APIRouter()

_VALID_STATUS = {0, 1, 2, 3, 4}
_VALID_SLOTS = {"上午", "下午", "晚上"}


@router.post("/create")
def create_appointment(req: AppointmentCreate, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """创建预约"""
    if req.time_slot not in _VALID_SLOTS:
        raise HTTPException(status_code=400, detail="时段仅支持：上午、下午、晚上")
    if req.visit_date < date.today():
        raise HTTPException(status_code=400, detail="就诊日期不能早于今天")
    doctor = db.query(Doctor).filter(Doctor.id == req.doctor_id, Doctor.status == 1).first()
    if not doctor:
        raise HTTPException(status_code=400, detail="医生不存在或已停用")
    dept = db.query(Department).filter(Department.id == req.department_id, Department.status == 1).first()
    if not dept:
        raise HTTPException(status_code=400, detail="科室不存在或已停用")
    if doctor.department_id and doctor.department_id != req.department_id:
        raise HTTPException(status_code=400, detail="医生与所选科室不匹配")
    # 患者同一日期时段只能保留一个有效预约，避免时间冲突和爽约占号。
    patient_conflict = db.query(Appointment).filter(
        Appointment.user_id == current.user_id,
        Appointment.visit_date == req.visit_date,
        Appointment.time_slot == req.time_slot,
        Appointment.status.in_((0, 1)),
    ).first()
    if patient_conflict:
        conflict_doctor = db.query(Doctor).filter(Doctor.id == patient_conflict.doctor_id).first()
        doctor_name = conflict_doctor.real_name or conflict_doctor.username if conflict_doctor else "其他医生"
        if patient_conflict.doctor_id == req.doctor_id:
            detail = (
                f"您已预约 {doctor_name}（{format_date(req.visit_date)} {req.time_slot}），"
                "不能重复预约；如需改约，请先取消原预约"
            )
        else:
            detail = (
                f"您在 {format_date(req.visit_date)} {req.time_slot} 已有 {doctor_name} 的预约，"
                "该时段不能同时预约其他医生"
            )
        raise HTTPException(status_code=400, detail=detail)
    schedule = db.query(DoctorSchedule).filter_by(
        doctor_id=req.doctor_id, work_date=req.visit_date, time_slot=req.time_slot, status=1
    ).first()
    if not schedule:
        raise HTTPException(status_code=400, detail="该医生此日期时段暂无可预约号源")
    used = db.query(Appointment.id).filter(
        Appointment.doctor_id == req.doctor_id, Appointment.visit_date == req.visit_date,
        Appointment.time_slot == req.time_slot, Appointment.status.in_((0, 1, 2)),
    ).count()
    if used >= schedule.capacity:
        raise HTTPException(status_code=400, detail="该时段号源已满")
    appt = Appointment(
        user_id=current.user_id, doctor_id=req.doctor_id,
        department_id=req.department_id, visit_date=req.visit_date,
        time_slot=req.time_slot, remark=req.remark,
    )
    db.add(appt)
    db.commit()
    return success({"id": appt.id}, "预约成功")


@router.get("/available-schedules")
def available_schedules(
    doctor_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(require_roles("user")),
):
    """获取医生未来仍有余量的可预约排班。"""
    doctor = db.query(Doctor.id).filter(Doctor.id == doctor_id, Doctor.status == 1).first()
    if not doctor:
        raise HTTPException(status_code=400, detail="医生不存在或已停用")

    schedules = db.query(DoctorSchedule).filter(
        DoctorSchedule.doctor_id == doctor_id,
        DoctorSchedule.work_date >= date.today(),
        DoctorSchedule.status == 1,
    ).order_by(DoctorSchedule.work_date, DoctorSchedule.id).all()

    data = []
    for schedule in schedules:
        used = db.query(Appointment.id).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.visit_date == schedule.work_date,
            Appointment.time_slot == schedule.time_slot,
            Appointment.status.in_((0, 1, 2)),
        ).count()
        remaining = max(schedule.capacity - used, 0)
        if remaining:
            conflict = db.query(Appointment.id).filter(
                Appointment.user_id == current.user_id,
                Appointment.visit_date == schedule.work_date,
                Appointment.time_slot == schedule.time_slot,
                Appointment.status.in_((0, 1)),
            ).first()
            data.append({
                "date": format_date(schedule.work_date),
                "time_slot": schedule.time_slot,
                "capacity": schedule.capacity,
                "remaining": remaining,
                "bookable": conflict is None,
                "unavailable_reason": "您在该日期时段已有待处理预约" if conflict else None,
            })
    return success(data)


@router.get("/my")
def my_appointments(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """我的预约"""
    items = db.query(Appointment).filter(Appointment.user_id == current.user_id).order_by(Appointment.id.desc()).all()
    return success(_format_appts(items, db))


@router.put("/my/{appt_id}/cancel")
def cancel_my_appointment(appt_id: int, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    """患者取消自己的预约（仅待确认/已确认）"""
    appt = db.query(Appointment).filter(
        Appointment.id == appt_id,
        Appointment.user_id == current.user_id,
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="预约不存在")
    if appt.status not in (0, 1):
        raise HTTPException(status_code=400, detail="当前状态不可取消")
    appt.status = 3
    db.commit()
    return success(None, "预约已取消")


@router.get("/doctor/my")
def doctor_appointments(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("doctor"))):
    """医生的预约"""
    items = db.query(Appointment).filter(Appointment.doctor_id == current.user_id).order_by(Appointment.id.desc()).all()
    return success(_format_appts(items, db))


@router.get("/admin/list")
def admin_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query(""),
    department_id: int = Query(None),
    visit_date: date = Query(None),
    status: int = Query(None),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员预约列表（支持模糊搜索与分页）"""
    q = db.query(Appointment)
    if keyword:
        q = (
            q.outerjoin(User, Appointment.user_id == User.id)
            .outerjoin(Doctor, Appointment.doctor_id == Doctor.id)
            .filter(
                or_(
                    User.username.contains(keyword),
                    User.real_name.contains(keyword),
                    Doctor.real_name.contains(keyword),
                    Appointment.remark.contains(keyword),
                )
            )
            .distinct()
        )
    if department_id is not None:
        q = q.filter(Appointment.department_id == department_id)
    if visit_date is not None:
        q = q.filter(Appointment.visit_date == visit_date)
    if status is not None:
        q = q.filter(Appointment.status == status)
    total = q.count()
    items = q.order_by(Appointment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_result(_format_appts(items, db), total, page, page_size)


@router.delete("/admin/{appt_id}")
def admin_delete_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员删除预约记录"""
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="预约记录不存在")
    db.delete(appt)
    db.commit()
    return success(None, "删除成功")


@router.put("/{appt_id}/status")
def update_status(appt_id: int, status: int, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("admin", "doctor"))):
    """更新预约状态"""
    if status not in _VALID_STATUS:
        raise HTTPException(status_code=400, detail="无效的预约状态")
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="预约不存在")
    if current.role == "doctor" and appt.doctor_id != current.user_id:
        raise HTTPException(status_code=403, detail="无权修改其他医生的预约")
    # 状态只能沿预约生命周期向前推进，取消和完成后不可重新开启。
    allowed_transitions = {
        0: {0, 1, 3},  # 待确认 -> 确认/取消
        1: {1, 2, 3},  # 已确认 -> 完成/取消
        2: {2},       # 已完成
        3: {3},       # 已取消
    }
    if status not in allowed_transitions.get(appt.status, set()):
        raise HTTPException(status_code=400, detail="不允许的预约状态流转")
    appt.status = status
    if status in (1, 2, 3, 4):
        db.add(Notification(user_id=appt.user_id, title="预约状态更新", content=f"您的预约已更新为：{ {1:'已确认',2:'已完成',3:'已取消',4:'爽约'}[status] }", type="appointment"))
    db.add(AuditLog(actor_id=current.user_id, actor_role=current.role, action="update_status", target_type="appointment", target_id=appt.id, detail=str(status)))
    db.commit()
    return success(None, "状态更新成功")


@router.post("/admin/schedules")
def create_schedule(doctor_id: int, work_date: date, time_slot: str, capacity: int = 1, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("admin"))):
    if time_slot not in _VALID_SLOTS or capacity < 1 or capacity > 100:
        raise HTTPException(status_code=400, detail="排班时段或号源数量无效")
    if not db.query(Doctor.id).filter(Doctor.id == doctor_id, Doctor.status == 1).first():
        raise HTTPException(status_code=400, detail="医生不存在或已停用")
    row = DoctorSchedule(doctor_id=doctor_id, work_date=work_date, time_slot=time_slot, capacity=capacity)
    db.add(row); db.add(AuditLog(actor_id=current.user_id, actor_role=current.role, action="create_schedule", target_type="schedule", detail=f"doctor={doctor_id}")); db.commit(); db.refresh(row)
    return success({"id": row.id}, "排班创建成功")


@router.get("/admin/schedules")
def list_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("admin")),
):
    """管理员排班列表"""
    query = db.query(DoctorSchedule)
    total = query.count()
    rows = query.order_by(DoctorSchedule.work_date.desc(), DoctorSchedule.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    doctor_ids = {row.doctor_id for row in rows}
    doctor_map = {
        doctor.id: doctor.real_name or doctor.username
        for doctor in db.query(Doctor).filter(Doctor.id.in_(doctor_ids)).all()
    } if doctor_ids else {}
    items = [{
        "id": row.id,
        "doctor_id": row.doctor_id,
        "doctor_name": doctor_map.get(row.doctor_id, ""),
        "work_date": format_date(row.work_date),
        "time_slot": row.time_slot,
        "capacity": row.capacity,
        "status": row.status,
    } for row in rows]
    return page_result(items, total, page, page_size)


@router.put("/admin/schedules/{schedule_id}/status")
def update_schedule_status(schedule_id: int, status: int, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("admin"))):
    if status not in (0, 1):
        raise HTTPException(status_code=400, detail="排班状态无效")
    row = db.query(DoctorSchedule).filter(DoctorSchedule.id == schedule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="排班不存在")
    row.status = status
    db.add(AuditLog(actor_id=current.user_id, actor_role=current.role, action="update_schedule_status", target_type="schedule", target_id=row.id, detail=str(status)))
    db.commit()
    return success(None, "排班状态已更新")

@router.put("/admin/schedules/{schedule_id}")
def edit_schedule(schedule_id: int, doctor_id: int, work_date: date, time_slot: str, capacity: int = 1, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    if time_slot not in _VALID_SLOTS or not 1 <= capacity <= 100:
        raise HTTPException(status_code=400, detail="排班参数无效")
    row = db.query(DoctorSchedule).filter(DoctorSchedule.id == schedule_id).first()
    if not row: raise HTTPException(status_code=404, detail="排班不存在")
    row.doctor_id, row.work_date, row.time_slot, row.capacity = doctor_id, work_date, time_slot, capacity
    db.commit(); return success(None, "排班已更新")

@router.delete("/admin/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles("admin"))):
    row = db.query(DoctorSchedule).filter(DoctorSchedule.id == schedule_id).first()
    if not row: raise HTTPException(status_code=404, detail="排班不存在")
    db.delete(row); db.commit(); return success(None, "排班已删除")


@router.post("/admin/close-expired")
def close_expired(db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("admin"))):
    cutoff = datetime.now() - timedelta(days=1)
    rows = db.query(Appointment).filter(Appointment.status.in_((0, 1)), Appointment.visit_date < date.today()).all()
    for row in rows:
        row.status = 4
        db.add(Notification(user_id=row.user_id, title="预约爽约记录", content="您有一条逾期未就诊预约，已标记为爽约", type="appointment"))
    db.add(AuditLog(actor_id=current.user_id, actor_role=current.role, action="close_expired", target_type="appointment", detail=str(len(rows))))
    db.commit(); return success({"count": len(rows)}, "逾期预约处理完成")


def _format_appts(items, db):
    """格式化预约列表"""
    if not items:
        return []
    user_ids = {a.user_id for a in items}
    doctor_ids = {a.doctor_id for a in items}
    dept_ids = {a.department_id for a in items}
    user_map = {
        u.id: u.real_name or u.username
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    }
    doctor_map = {
        d.id: d.real_name
        for d in db.query(Doctor).filter(Doctor.id.in_(doctor_ids)).all()
    }
    dept_map = {
        d.id: d.name
        for d in db.query(Department).filter(Department.id.in_(dept_ids)).all()
    }
    return [{
        "id": a.id, "user_id": a.user_id, "user_name": user_map.get(a.user_id, ""),
        "doctor_id": a.doctor_id, "doctor_name": doctor_map.get(a.doctor_id, ""),
        "department_id": a.department_id, "department_name": dept_map.get(a.department_id, ""),
        "visit_date": format_date(a.visit_date), "time_slot": a.time_slot,
        "status": a.status, "remark": a.remark,
        "create_time": format_datetime(a.create_time),
    } for a in items]
