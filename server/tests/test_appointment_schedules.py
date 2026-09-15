from datetime import date, timedelta

from models.appointment import Appointment
from models.department import Department
from models.doctor import Doctor
from models.operations import DoctorSchedule


def test_available_schedules_and_capacity_booking(client, db_session, auth_headers):
    visit_date = date.today() + timedelta(days=1)
    doctor = db_session.get(Doctor, 2)
    doctor.department_id = 10
    db_session.add(Department(id=10, name="心血管内科", status=1))
    db_session.add(DoctorSchedule(
        doctor_id=2,
        work_date=visit_date,
        time_slot="上午",
        capacity=2,
        status=1,
    ))
    db_session.add(Appointment(
        user_id=99,
        doctor_id=2,
        department_id=10,
        visit_date=visit_date,
        time_slot="上午",
        status=0,
    ))
    db_session.commit()

    response = client.get(
        "/api/v1/appointments/available-schedules",
        params={"doctor_id": 2},
        headers=auth_headers("user"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == [{
        "date": visit_date.isoformat(),
        "time_slot": "上午",
        "capacity": 2,
        "remaining": 1,
        "bookable": True,
        "unavailable_reason": None,
    }]

    create_response = client.post(
        "/api/v1/appointments/create",
        headers=auth_headers("user"),
        json={
            "doctor_id": 2,
            "department_id": 10,
            "visit_date": visit_date.isoformat(),
            "time_slot": "上午",
            "remark": "咳嗽",
        },
    )

    assert create_response.status_code == 200, create_response.text


def test_full_schedule_is_not_available(client, db_session, auth_headers):
    visit_date = date.today() + timedelta(days=1)
    db_session.add(DoctorSchedule(
        doctor_id=2,
        work_date=visit_date,
        time_slot="下午",
        capacity=1,
        status=1,
    ))
    db_session.add(Appointment(
        user_id=99,
        doctor_id=2,
        department_id=10,
        visit_date=visit_date,
        time_slot="下午",
        status=0,
    ))
    db_session.commit()

    response = client.get(
        "/api/v1/appointments/available-schedules",
        params={"doctor_id": 2},
        headers=auth_headers("user"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == []


def test_duplicate_booking_has_clear_reason(client, db_session, auth_headers):
    visit_date = date.today() + timedelta(days=1)
    doctor = db_session.get(Doctor, 2)
    doctor.department_id = 10
    db_session.add(Department(id=10, name="心血管内科", status=1))
    db_session.add(DoctorSchedule(
        doctor_id=2,
        work_date=visit_date,
        time_slot="晚上",
        capacity=3,
        status=1,
    ))
    db_session.add(Appointment(
        user_id=1,
        doctor_id=2,
        department_id=10,
        visit_date=visit_date,
        time_slot="晚上",
        status=0,
    ))
    db_session.commit()

    schedules_response = client.get(
        "/api/v1/appointments/available-schedules",
        params={"doctor_id": 2},
        headers=auth_headers("user"),
    )
    slot = schedules_response.json()["data"][0]
    assert slot["remaining"] == 2
    assert slot["bookable"] is False
    assert slot["unavailable_reason"] == "您在该日期时段已有待处理预约"

    create_response = client.post(
        "/api/v1/appointments/create",
        headers=auth_headers("user"),
        json={
            "doctor_id": 2,
            "department_id": 10,
            "visit_date": visit_date.isoformat(),
            "time_slot": "晚上",
        },
    )

    assert create_response.status_code == 400
    assert create_response.json()["detail"] == (
        f"您已预约 医生（{visit_date.isoformat()} 晚上），"
        "不能重复预约；如需改约，请先取消原预约"
    )
