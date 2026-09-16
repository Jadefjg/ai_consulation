from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1 import p3
from db.session import get_db
from models.p3 import ChronicRecord, FollowupPlan, FollowupTask


def test_patient_followup_complete_rolls_next_task(db_session, auth_headers):
    plan = FollowupPlan(
        user_id=1,
        doctor_id=2,
        title="血压随访",
        frequency_days=30,
        next_date=date.today(),
        status=1,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    task = FollowupTask(plan_id=plan.id, due_date=date.today(), status=0)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    app = FastAPI()
    app.include_router(p3.router, prefix="/api/v1/p3")

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        forbidden = client.post(
            f"/api/v1/p3/followups/{task.id}/complete",
            json={"response": "医生不能替患者完成"},
            headers=auth_headers("doctor"),
        )
        assert forbidden.status_code == 403

        response = client.post(
            f"/api/v1/p3/followups/{task.id}/complete",
            json={"response": "血压平稳，已按时服药"},
            headers=auth_headers("user"),
        )
        assert response.status_code == 200, response.text
        listed = client.get("/api/v1/p3/followups", headers=auth_headers("user"))
        assert listed.status_code == 200
        item = listed.json()["data"][0]
        assert item["can_complete"] is True
        assert item["next_date"] == str(date.today() + timedelta(days=30))


def test_patient_chronic_metric_and_risk(db_session, auth_headers):
    db_session.add(ChronicRecord(user_id=1, disease="高血压", status=1))
    db_session.commit()

    app = FastAPI()
    app.include_router(p3.router, prefix="/api/v1/p3")

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        created = client.post("/api/v1/p3/chronic", json={"disease": "糖尿病"}, headers=auth_headers("user"))
        assert created.status_code == 200, created.text
        chronic_id = created.json()["data"]["id"]
        metric = client.post(
            f"/api/v1/p3/chronic/{chronic_id}/metrics",
            json={"metric": "空腹血糖", "value": "6.2"},
            headers=auth_headers("user"),
        )
        assert metric.status_code == 200, metric.text
        listed = client.get("/api/v1/p3/chronic", headers=auth_headers("user"))
        diseases = {row["disease"] for row in listed.json()["data"]}
        assert "糖尿病" in diseases
        assert "高血压" in diseases
        risk = client.post(
            "/api/v1/p3/risk/assess",
            json={"factors": {"age": 70, "chronic_count": 2, "severe": True}},
            headers=auth_headers("user"),
        )
        assert risk.status_code == 200
        assert risk.json()["data"]["level"] in {"中风险", "高风险"}
