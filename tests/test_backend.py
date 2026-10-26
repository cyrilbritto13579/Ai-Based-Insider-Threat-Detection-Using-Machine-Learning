"""
Automated Test Suite for Backend & ML Pipeline
==============================================
Phase 20: Comprehensive tests for data models, feature extraction, ML inference,
dynamic risk scoring, SHAP explainability, alert generation, and scenario simulation.
"""

import sys
import os
import pytest
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.db.session import init_db, SessionLocal
from app.db.models import User, ActivityEvent, RiskScore, Alert
from app.simulation.enterprise import seed_synthetic_enterprise
from app.simulation.scenarios import generate_scenario_events, SCENARIO_METADATA
from app.ml.features import extract_user_features
from app.ml.inference import inference_engine
from app.ml.explainability import shap_service
from app.risk.engine import risk_engine
from app.risk.alerts import alert_engine


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    seed_synthetic_enterprise(db)
    yield db
    db.close()


def test_synthetic_enterprise_seeding(db_session):
    """Verify that TechNova users are properly seeded with baselines."""
    users = db_session.query(User).all()
    assert len(users) >= 7
    user_ids = [u.user_id for u in users]
    assert "ENG-001" in user_ids
    assert "ENG-014" in user_ids
    assert "FIN-001" in user_ids

    elevated_users = (
        db_session.query(User)
        .filter(User.user_id.in_(["ENG-013", "FIN-006", "HR-004"]))
        .all()
    )
    assert len(elevated_users) == 3
    assert all(user.risk_score.current_risk_tier == "CRITICAL" for user in elevated_users)
    assert all(user.risk_score.current_risk_score == 82 for user in elevated_users)

    # Check baseline structure
    eng = db_session.query(User).filter(User.user_id == "ENG-001").first()
    b = eng.get_baseline_dict()
    assert "logon_mean" in b
    assert "email_mean" in b


def test_feature_extraction(db_session):
    """Verify that 58 features matching feature_schema.json are extracted."""
    user = db_session.query(User).filter(User.user_id == "ENG-001").first()
    events = [
        ActivityEvent(
            event_id="EVT-T1",
            timestamp=datetime(2026, 9, 1, 9, 0),
            user_id="ENG-001",
            pc="PC-ENG-01",
            activity_type="LOGIN",
            is_after_hours=False,
            is_weekend=False,
        ),
        ActivityEvent(
            event_id="EVT-T2",
            timestamp=datetime(2026, 9, 1, 10, 0),
            user_id="ENG-001",
            pc="PC-ENG-01",
            activity_type="FILE_ACCESS",
            is_after_hours=False,
            is_weekend=False,
        ),
    ]
    features = extract_user_features(user, events, events[-1])
    assert len(features) == 58
    assert "logon_count" in features
    assert "device_connect_count" in features
    assert "overall_behavior_deviation" in features


def test_ml_inference(db_session):
    """Verify ML model produces valid probability and threshold prediction."""
    user = db_session.query(User).filter(User.user_id == "ENG-001").first()
    events = [
        ActivityEvent(
            event_id="EVT-T1",
            timestamp=datetime.utcnow(),
            user_id="ENG-001",
            pc="PC-ENG-01",
            activity_type="LOGIN",
            is_after_hours=False,
            is_weekend=False,
        )
    ]
    features = extract_user_features(user, events, events[0])
    prob, pred, vec = inference_engine.predict(features)
    assert 0.0 <= prob <= 1.0
    assert pred in [0, 1]
    assert len(vec) == 58


def test_dynamic_risk_engine():
    """Verify 0-100 score bounds and tier classifications."""
    # Test 1: Normal activity -> LOW
    score, tier, dev, heur = risk_engine.compute_risk(
        ml_probability=0.01,
        features={"overall_behavior_deviation": 0.1, "afterhours_triple_signal": 0.0}
    )
    assert 0 <= score <= 29
    assert tier == "LOW"

    # Test 2: Severe exfiltration scenario -> HIGH or CRITICAL
    score, tier, dev, heur = risk_engine.compute_risk(
        ml_probability=0.85,
        features={
            "overall_behavior_deviation": 3.5,
            "afterhours_triple_signal": 1.0,
            "file_access_count": 20.0,
            "device_connect_count": 2.0,
            "email_external_to": 1.0,
            "email_with_attachment": 1.0,
        }
    )
    assert score >= 70
    assert tier in ["HIGH", "CRITICAL"]


def test_shap_explainability(db_session):
    """Verify SHAP produces compliant, non-accusatory security explanations."""
    user = db_session.query(User).filter(User.user_id == "ENG-014").first()
    events = [
        ActivityEvent(
            event_id="EVT-T1",
            timestamp=datetime.utcnow().replace(hour=23),
            user_id="ENG-014",
            pc="PC-ENG-14",
            activity_type="DEVICE_CONNECT",
            is_after_hours=True,
            is_weekend=False,
        )
    ]
    features = extract_user_features(user, events, events[0])
    _, _, vec = inference_engine.predict(features)
    explanation, top_factors, base_val = shap_service.explain_instance(vec, top_n=5)
    assert isinstance(explanation, str)
    assert "malicious" not in explanation.lower() or "not" in explanation.lower() or "suspicious" in explanation.lower()
    assert len(top_factors) <= 5


def test_simulation_scenarios():
    """Verify all 6 scenarios generate structured event sequences."""
    for meta in SCENARIO_METADATA:
        events = generate_scenario_events(meta["id"], "ENG-001", "PC-ENG-01")
        assert len(events) > 0
        for e in events:
            assert "event_id" in e
            assert "activity_type" in e
            assert "timestamp" in e
