"""轻量进程内调度器；生产环境建议改用 Celery/APScheduler。"""
import asyncio
from datetime import date, datetime, timedelta
from db.session import SessionLocal
from models.appointment import Appointment
from models.operations import Notification
from models.doctor_consult import DoctorConsult

async def expired_appointment_worker(stop: asyncio.Event):
    while not stop.is_set():
        db = SessionLocal()
        try:
            rows = db.query(Appointment).filter(Appointment.status.in_((0, 1)), Appointment.visit_date < date.today()).all()
            for row in rows:
                row.status = 4
                db.add(Notification(user_id=row.user_id, title="预约已标记爽约", content="逾期未就诊的预约已自动标记为爽约", type="appointment"))
            if rows: db.commit()
            cutoff = datetime.now() - timedelta(hours=24)
            overdue = db.query(DoctorConsult).filter(DoctorConsult.status == 0, DoctorConsult.create_time < cutoff).all()
            for row in overdue:
                row.status = 3
                if row.doctor_id:
                    db.add(Notification(user_id=row.doctor_id, title="咨询接诊已超时", content="您有一条超过24小时未处理的患者咨询，请尽快接诊。", type="consult_timeout"))
            if overdue: db.commit()
        finally:
            db.close()
        try:
            await asyncio.wait_for(stop.wait(), timeout=300)
        except asyncio.TimeoutError:
            pass
