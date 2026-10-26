"""
End-to-End API Integration & Simulation Test
============================================
Tests live API endpoints, event ingestion, risk score calculation, and simulation controls.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.main import app
from app.db.session import init_db, SessionLocal
from app.simulation.enterprise import seed_synthetic_enterprise

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    db = SessionLocal()
    seed_synthetic_enterprise(db)
    db.close()


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_users_endpoints():
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 7

    user_id = users[0]["user_id"]
    detail_res = client.get(f"/api/v1/users/{user_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["user_id"] == user_id
    assert "baseline_stats" in detail


def test_explain_endpoint():
    response = client.get("/api/v1/users/ENG-001/explain")
    assert response.status_code == 200
    data = response.json()
    assert "text_explanation" in data
    assert "top_factors" in data


def test_employee_report_download():
    response = client.get("/api/v1/users/ENG-013/report")
    assert response.status_code == 200
    assert "attachment; filename=\"employee-activity-report-ENG-013.html\"" in response.headers["content-disposition"]
    assert "Employee Activity &amp; Risk Report" in response.text
    assert "Risk Analysis" in response.text
    assert "Recent Activity Events" in response.text


def test_employee_report_unknown_user():
    response = client.get("/api/v1/users/UNKNOWN-USER/report")
    assert response.status_code == 404


def test_model_metrics_endpoint():
    response = client.get("/api/v1/model/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["best_model_name"] == "XGBoost"
    assert len(data["comparison_table"]) == 3
    assert data["optimal_threshold"] > 0.0


def test_simulation_status():
    response = client.get("/api/v1/simulation/status")
    assert response.status_code == 200
    data = response.json()
    assert len(data["available_scenarios"]) == 6


def test_manual_event_injection():
    event_payload = {
        "user_id": "ENG-014",
        "pc": "PC-ENG-14",
        "activity_type": "DEVICE_CONNECT",
        "details": {"device_name": "SanDisk Extreme 64GB", "device_type": "USB"}
    }
    response = client.post("/api/v1/simulation/inject", json=event_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "PIPELINE_UPDATE"
    assert "risk" in data
    assert "risk_score" in data["risk"]
