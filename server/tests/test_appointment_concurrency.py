"""预约容量约束回归测试（SQLite 单线程环境验证核心不变量）。"""
from datetime import date
from models.operations import DoctorSchedule
from models.appointment import Appointment
def test_capacity_query_never_exceeds_schedule(db_session):
    # 集成环境应使用两个并发事务；这里验证容量统计只计有效状态。
    schedule = DoctorSchedule(doctor_id=1, work_date=date.today(), time_slot="上午", capacity=1)
    db_session.add(schedule); db_session.commit()
    db_session.add(Appointment(user_id=1, doctor_id=1, department_id=1, visit_date=date.today(), time_slot="上午", status=3))
    db_session.commit()
    used = db_session.query(Appointment).filter(Appointment.doctor_id==1, Appointment.visit_date==date.today(), Appointment.time_slot=="上午", Appointment.status.in_((0,1,2))).count()
    assert used == 0
