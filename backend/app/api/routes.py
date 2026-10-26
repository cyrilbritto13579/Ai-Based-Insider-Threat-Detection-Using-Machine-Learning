"""
FastAPI Route Endpoints
=======================
Defines clean RESTful API routes and WebSocket handlers for the SOC dashboard.
"""

import json
import os
from html import escape
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.db.session import get_db, SessionLocal
from app.db.models import User, ActivityEvent, RiskScore, RiskHistory, Alert, AdminAction
from app.core.config import settings
from app.schemas import (
    UserResponse,
    UserDetailResponse,
    ActivityEventCreate,
    ActivityEventResponse,
    RiskScoreResponse,
    RiskHistoryPoint,
    RiskOverviewResponse,
    AlertResponse,
    AlertAcknowledgeRequest,
    SimulationStatusResponse,
    SimulationStartRequest,
    ModelMetricsResponse,
    ShapExplanationResponse,
)
from app.services.pipeline_service import pipeline_service
from app.simulation.manager import simulation_manager
from app.ml.explainability import shap_service
from app.ml.features import extract_user_features
from app.ml.inference import inference_engine
from app.risk.threshold_service import threshold_service

api_router = APIRouter()


# ---------------------------------------------------------------------------
# 1. Health & Status
# ---------------------------------------------------------------------------
@api_router.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(func.now()) if "sqlite" not in settings.DATABASE_URL else db.query(User).count()
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db_ok else "disconnected",
        "ml_engine": "XGBoost (Active)" if inference_engine.model is not None else "Fallback",
        "websocket_clients": len(pipeline_service.active_websockets),
        "version": settings.VERSION,
    }


# ---------------------------------------------------------------------------
# 2. Users & Investigation
# ---------------------------------------------------------------------------
@api_router.get("/users", response_model=List[UserResponse], tags=["Users"])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    results = []
    for u in users:
        risk = u.risk_score
        results.append(
            UserResponse(
                id=u.id,
                user_id=u.user_id,
                name=u.name,
                department=u.department,
                role=u.role,
                email=u.email,
                assigned_pc=u.assigned_pc,
                is_synthetic=u.is_synthetic,
                manager=u.manager or "",
                location=u.location or "",
                employment_type=u.employment_type or "Full-Time",
                join_date=u.join_date or "",
                normal_hours=u.normal_hours or "09:00–18:00",
                account_status=u.account_status or "ACTIVE",
                current_risk_score=risk.current_risk_score if risk else 10,
                current_risk_tier=risk.current_risk_tier if risk else "LOW",
                ml_probability=risk.ml_probability if risk else 0.0,
                last_updated=risk.last_updated if risk else u.created_at,
            )
        )
    # Sort highest risk first
    results.sort(key=lambda x: x.current_risk_score, reverse=True)
    return results


@api_router.get("/users/{user_id}", response_model=UserDetailResponse, tags=["Users"])
def get_user_detail(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    risk = user.risk_score
    recent_events_cnt = db.query(ActivityEvent).filter(ActivityEvent.user_id == user_id).count()
    alerts_cnt = db.query(Alert).filter(Alert.user_id == user_id).count()

    # Count activity types
    login_count = db.query(ActivityEvent).filter(
        ActivityEvent.user_id == user_id,
        ActivityEvent.activity_type.in_(["LOGIN", "LOGON"])
    ).count()
    device_count = db.query(ActivityEvent).filter(
        ActivityEvent.user_id == user_id,
        ActivityEvent.activity_type.in_(["DEVICE_CONNECT", "DEVICE_DISCONNECT"])
    ).count()
    file_count = db.query(ActivityEvent).filter(
        ActivityEvent.user_id == user_id,
        ActivityEvent.activity_type.in_(["FILE_ACCESS", "FILE_COPY"])
    ).count()
    email_count = db.query(ActivityEvent).filter(
        ActivityEvent.user_id == user_id,
        ActivityEvent.activity_type.in_(["EMAIL_ACTIVITY", "EMAIL_SEND"])
    ).count()

    # Get last activity timestamp
    last_event = db.query(ActivityEvent).filter(
        ActivityEvent.user_id == user_id
    ).order_by(ActivityEvent.timestamp.desc()).first()

    return UserDetailResponse(
        id=user.id,
        user_id=user.user_id,
        name=user.name,
        department=user.department,
        role=user.role,
        email=user.email,
        assigned_pc=user.assigned_pc,
        is_synthetic=user.is_synthetic,
        manager=user.manager or "",
        location=user.location or "",
        employment_type=user.employment_type or "Full-Time",
        join_date=user.join_date or "",
        normal_hours=user.normal_hours or "09:00–18:00",
        account_status=user.account_status or "ACTIVE",
        current_risk_score=risk.current_risk_score if risk else 10,
        current_risk_tier=risk.current_risk_tier if risk else "LOW",
        ml_probability=risk.ml_probability if risk else 0.0,
        last_updated=risk.last_updated if risk else user.created_at,
        baseline_stats=user.get_baseline_dict(),
        explanation=risk.explanation if risk else "Normal baseline behavior observed.",
        top_factors=risk.get_top_factors_list() if risk else [],
        recent_events_count=recent_events_cnt,
        total_alerts_count=alerts_cnt,
        login_count=login_count,
        device_count=device_count,
        file_count=file_count,
        email_count=email_count,
        last_activity=last_event.timestamp.isoformat() if last_event else None,
    )


@api_router.get("/users/{user_id}/timeline", response_model=List[RiskHistoryPoint], tags=["Users"])
def get_user_risk_timeline(user_id: str, db: Session = Depends(get_db)):
    history = (
        db.query(RiskHistory)
        .filter(RiskHistory.user_id == user_id)
        .order_by(RiskHistory.timestamp.asc())
        .limit(100)
        .all()
    )
    return [
        RiskHistoryPoint(
            timestamp=h.timestamp,
            risk_score=h.risk_score,
            risk_tier=h.risk_tier,
            ml_probability=h.ml_probability,
        )
        for h in history
    ]


@api_router.get("/users/{user_id}/events", response_model=List[ActivityEventResponse], tags=["Users"])
def get_user_events(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    events = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.user_id == user_id)
        .order_by(ActivityEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        ActivityEventResponse(
            id=e.id,
            event_id=e.event_id,
            timestamp=e.timestamp,
            user_id=e.user_id,
            pc=e.pc,
            activity_type=e.activity_type,
            details=e.get_details_dict(),
            is_after_hours=e.is_after_hours,
            is_weekend=e.is_weekend,
        )
        for e in events
    ]


@api_router.get("/users/{user_id}/report", tags=["Users"])
def download_user_report(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    risk = user.risk_score
    events = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.user_id == user_id)
        .order_by(ActivityEvent.timestamp.desc())
        .limit(500)
        .all()
    )
    history = (
        db.query(RiskHistory)
        .filter(RiskHistory.user_id == user_id)
        .order_by(RiskHistory.timestamp.desc())
        .limit(100)
        .all()
    )
    alerts = (
        db.query(Alert)
        .filter(Alert.user_id == user_id)
        .order_by(Alert.timestamp.desc())
        .limit(100)
        .all()
    )

    def table_row(values):
        cells = "".join(f"<td>{escape(str(value if value is not None else ''))}</td>" for value in values)
        return f"<tr>{cells}</tr>"

    factors = risk.get_top_factors_list() if risk else []
    factor_rows = "".join(
        table_row([
            factor.get("feature", "").replace("_", " "),
            factor.get("value", ""),
            factor.get("impact_score", ""),
            factor.get("direction", ""),
        ])
        for factor in factors
    ) or '<tr><td colspan="4">No contributing factors recorded.</td></tr>'
    alert_rows = "".join(
        table_row([
            alert.timestamp.isoformat(),
            f"{alert.risk_tier} · {alert.risk_score}",
            alert.status,
            alert.behavior,
            alert.primary_reason,
        ])
        for alert in alerts
    ) or '<tr><td colspan="5">No associated alerts.</td></tr>'
    event_rows = "".join(
        table_row([
            event.timestamp.isoformat(),
            event.activity_type,
            event.pc,
            json.dumps(event.get_details_dict(), ensure_ascii=False),
            "Yes" if event.is_after_hours else "No",
        ])
        for event in events
    ) or '<tr><td colspan="5">No activity events available.</td></tr>'
    history_rows = "".join(
        table_row([
            point.timestamp.isoformat(),
            point.risk_score,
            point.risk_tier,
            f"{round(point.ml_probability * 100)}%",
        ])
        for point in history
    ) or '<tr><td colspan="4">No risk history available.</td></tr>'

    current_score = risk.current_risk_score if risk else 10
    current_tier = risk.current_risk_tier if risk else "LOW"
    probability = round((risk.ml_probability if risk else 0.0) * 100)
    explanation = risk.explanation if risk else "Normal baseline behavior observed."
    latest_activity = events[0].timestamp.isoformat() if events else "None recorded"
    generated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    report = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Employee Activity Report - {escape(user.user_id)}</title>
<style>
body{{font:14px/1.5 Arial,sans-serif;color:#172033;margin:36px auto;max-width:1000px;padding:0 22px}}
h1,h2{{color:#12315b}}h1{{margin-bottom:4px}}.muted{{color:#596579}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:22px 0}}
.summary div{{border:1px solid #cbd5e1;border-radius:8px;padding:12px}}
.label{{font-size:11px;text-transform:uppercase;color:#596579}}strong{{display:block;font-size:18px;margin-top:4px}}
table{{border-collapse:collapse;width:100%;margin:12px 0 24px;font-size:12px}}
th,td{{border:1px solid #cbd5e1;padding:7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}
th{{background:#eaf1fb;color:#12315b}}.notice{{border-left:4px solid #2563eb;padding:10px 14px;background:#eff6ff}}
@media print{{body{{margin:0;max-width:none}}h2{{break-after:avoid}}tr{{break-inside:avoid}}}}
</style></head><body>
<h1>Employee Activity &amp; Risk Report</h1><p class="muted">Generated {escape(generated_at)} · {"Synthetic demonstration data" if user.is_synthetic else "Employee activity data"}</p>
<div class="summary"><div><span class="label">Employee</span><strong>{escape(user.name)}</strong>{escape(user.user_id)}</div>
<div><span class="label">Current risk</span><strong>{escape(current_tier)} · {current_score}/100</strong>ML probability {probability}%</div>
<div><span class="label">Account status</span><strong>{escape(user.account_status or "ACTIVE")}</strong>{len(alerts)} recent associated alerts</div></div>
<h2>Employee Profile</h2><p><b>Department:</b> {escape(user.department)} &nbsp; <b>Role:</b> {escape(user.role)} &nbsp; <b>Manager:</b> {escape(user.manager or "Not listed")}<br>
<b>Workstation:</b> {escape(user.assigned_pc)} &nbsp; <b>Normal hours:</b> {escape(user.normal_hours or "Not listed")} &nbsp; <b>Last activity:</b> {escape(latest_activity)}</p>
<h2>Risk Analysis</h2><p class="notice">{escape(explanation)}</p>
<table><thead><tr><th>Behavioral factor</th><th>Value</th><th>Impact</th><th>Direction</th></tr></thead><tbody>{factor_rows}</tbody></table>
<h2>Associated Alerts (latest {len(alerts)})</h2><table><thead><tr><th>Timestamp</th><th>Risk</th><th>Status</th><th>Behavior</th><th>Analysis</th></tr></thead><tbody>{alert_rows}</tbody></table>
<h2>Recent Activity Events (latest {len(events)})</h2><table><thead><tr><th>Timestamp</th><th>Activity</th><th>Workstation</th><th>Details</th><th>After hours</th></tr></thead><tbody>{event_rows}</tbody></table>
<h2>Risk History (latest {len(history)})</h2><table><thead><tr><th>Timestamp</th><th>Score</th><th>Tier</th><th>ML probability</th></tr></thead><tbody>{history_rows}</tbody></table>
<p class="muted">This report is an analytical aid. Risk indicators describe activity requiring review and are not a determination of employee intent.</p>
</body></html>"""

    safe_user_id = "".join(character for character in user.user_id if character.isalnum() or character in "-_")
    return Response(
        content=report,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="employee-activity-report-{safe_user_id}.html"'},
    )


@api_router.get("/users/{user_id}/explain", response_model=ShapExplanationResponse, tags=["Users"])
def explain_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recent_events = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.user_id == user_id)
        .order_by(ActivityEvent.timestamp.desc())
        .limit(50)
        .all()
    )
    latest_event = recent_events[0] if recent_events else None
    features = extract_user_features(user, recent_events, latest_event)
    ml_prob, _, feature_vec = inference_engine.predict(features)
    text_exp, top_factors, base_val = shap_service.explain_instance(feature_vec, top_n=8)
    risk = user.risk_score

    return ShapExplanationResponse(
        user_id=user.user_id,
        risk_score=risk.current_risk_score if risk else 10,
        risk_tier=risk.current_risk_tier if risk else "LOW",
        ml_probability=round(ml_prob, 4),
        text_explanation=text_exp,
        top_factors=top_factors,
        base_value=base_val,
    )


# ---------------------------------------------------------------------------
# 3. Alerts
# ---------------------------------------------------------------------------
@api_router.get("/alerts", response_model=List[AlertResponse], tags=["Alerts"])
def get_alerts(
    tier: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(Alert, User).join(User, Alert.user_id == User.user_id)

    if tier:
        query = query.filter(Alert.risk_tier == tier.upper())
    if status:
        query = query.filter(Alert.status == status.upper())
    if user_id:
        query = query.filter(Alert.user_id == user_id)

    alerts = query.order_by(desc(Alert.timestamp)).limit(limit).all()

    results = []
    for alert, user in alerts:
        results.append(
            AlertResponse(
                id=alert.id,
                alert_id=alert.alert_id,
                timestamp=alert.timestamp,
                user_id=alert.user_id,
                user_name=user.name,
                department=user.department,
                risk_score=alert.risk_score,
                risk_tier=alert.risk_tier,
                behavior=alert.behavior,
                primary_reason=alert.primary_reason,
                status=alert.status,
                notes=alert.notes or "",
                resolved_by=alert.resolved_by or "",
                details=json.loads(alert.details or "{}"),
            )
        )
    return results


@api_router.patch("/alerts/{alert_id}/acknowledge", tags=["Alerts"])
def acknowledge_alert(alert_id: str, req: AlertAcknowledgeRequest, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    valid_statuses = {"NEW", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"}
    if req.status.upper() not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    alert.status = req.status.upper()
    if req.notes:
        alert.notes = req.notes
    if req.resolved_by:
        alert.resolved_by = req.resolved_by
    db.commit()
    return {"status": "success", "alert_id": alert_id, "new_status": alert.status}


# ---------------------------------------------------------------------------
# 4. Risk Overview & Trends
# ---------------------------------------------------------------------------
@api_router.get("/risk/overview", response_model=RiskOverviewResponse, tags=["Risk"])
def get_risk_overview(db: Session = Depends(get_db)):
    users = db.query(User).all()
    total_users = len(users)
    total_events = db.query(ActivityEvent).count()
    crit_alerts = db.query(Alert).filter(Alert.risk_tier == "CRITICAL").count()

    tier_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    suspicious = 0
    for u in users:
        tier = u.risk_score.current_risk_tier if u.risk_score else "LOW"
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        if tier in ["HIGH", "CRITICAL"]:
            suspicious += 1

    open_alerts = db.query(Alert).filter(Alert.status.in_(["NEW", "ACKNOWLEDGED", "INVESTIGATING"])).count()

    return RiskOverviewResponse(
        total_monitored_users=total_users,
        total_events_analyzed=total_events,
        suspicious_users_count=suspicious,
        critical_alerts_count=crit_alerts,
        high_risk_count=tier_counts["HIGH"],
        medium_risk_count=tier_counts["MEDIUM"],
        low_risk_count=tier_counts["LOW"],
        open_alerts_count=open_alerts,
        tier_distribution=tier_counts,
        system_health={
            "api": "ONLINE",
            "database": "CONNECTED",
            "ml_engine": "ACTIVE (XGBoost)",
            "event_stream": simulation_manager.status,
        },
    )


# ---------------------------------------------------------------------------
# 5. Analytics
# ---------------------------------------------------------------------------
@api_router.get("/analytics/feature-importance", tags=["Analytics"])
def get_feature_importance():
    if os.path.exists(settings.SHAP_IMPORTANCE_PATH):
        try:
            with open(settings.SHAP_IMPORTANCE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass

    # Fallback to model feature importances
    if inference_engine.model and hasattr(inference_engine.model, "feature_importances_"):
        imps = inference_engine.model.feature_importances_
        feats = inference_engine.feature_schema
        ranked = sorted(zip(feats, imps), key=lambda x: x[1], reverse=True)
        return {
            "importance": [{"feature": f, "mean_abs_shap": round(float(v), 4)} for f, v in ranked],
            "explainer_type": "ModelGiniImportance",
        }

    return {"importance": []}


@api_router.get("/analytics/activity-distribution", tags=["Analytics"])
def get_activity_distribution(db: Session = Depends(get_db)):
    counts = (
        db.query(ActivityEvent.activity_type, func.count(ActivityEvent.id))
        .group_by(ActivityEvent.activity_type)
        .all()
    )
    return {act: cnt for act, cnt in counts}


# ---------------------------------------------------------------------------
# 6. Model Performance & Evaluation Metrics
# ---------------------------------------------------------------------------
@api_router.get("/model/metrics", response_model=ModelMetricsResponse, tags=["Model"])
def get_model_metrics():
    comparison_data = {}
    metadata = {}
    if os.path.exists(settings.COMPARISON_PATH):
        try:
            with open(settings.COMPARISON_PATH, "r") as f:
                comparison_data = json.load(f)
        except Exception:
            pass

    if os.path.exists(settings.METADATA_PATH):
        try:
            with open(settings.METADATA_PATH, "r") as f:
                metadata = json.load(f)
        except Exception:
            pass

    models_dict = comparison_data.get("models", {})
    comparison_table = []
    for name, info in models_dict.items():
        v_m = info.get("validation_metrics", {})
        t_m = info.get("test_metrics", {})
        comparison_table.append({
            "model_name": name,
            "model_type": info.get("model_type", "Classifier"),
            "is_best": info.get("is_best", False),
            "optimal_threshold": info.get("optimal_threshold", 0.5),
            "val_pr_auc": v_m.get("pr_auc", 0.0),
            "val_f1": v_m.get("f1", 0.0),
            "val_recall": v_m.get("recall", 0.0),
            "val_precision": v_m.get("precision", 0.0),
            "val_roc_auc": v_m.get("roc_auc", 0.0),
            "test_pr_auc": t_m.get("pr_auc", 0.0),
            "test_f1": t_m.get("f1", 0.0),
            "test_recall": t_m.get("recall", 0.0),
            "test_precision": t_m.get("precision", 0.0),
            "test_roc_auc": t_m.get("roc_auc", 0.0),
            "tp": t_m.get("tp", 0),
            "fp": t_m.get("fp", 0),
            "fn": t_m.get("fn", 0),
            "tn": t_m.get("tn", 0),
        })

    return ModelMetricsResponse(
        best_model_name=metadata.get("best_model_name", "XGBoost"),
        best_model_type=metadata.get("best_model_type", "XGBClassifier"),
        optimal_threshold=metadata.get("optimal_threshold", 0.1184),
        validation_metrics=metadata.get("validation_metrics", {}),
        test_metrics=metadata.get("test_metrics", {}),
        comparison_table=comparison_table,
        dataset_summary={
            "source": "CERT Insider Threat Dataset Release 4.2",
            "total_raw_events": 4335799,
            "user_day_samples": 330452,
            "train_samples": 209182,
            "val_samples": 56239,
            "test_samples": 65031,
            "features_engineered": 58,
            "imbalance_ratio": "268:1 (0.40% malicious)",
        },
    )


# ---------------------------------------------------------------------------
# 7. Live Simulation Controls
# ---------------------------------------------------------------------------
@api_router.get("/simulation/status", response_model=SimulationStatusResponse, tags=["Simulation"])
def get_simulation_status():
    return SimulationStatusResponse(**simulation_manager.get_status())


@api_router.post("/simulation/start", tags=["Simulation"])
async def start_simulation(req: SimulationStartRequest):
    res = await simulation_manager.start(
        scenario=req.scenario,
        target_user_id=req.target_user_id,
        speed_interval=req.speed_interval,
        max_events=req.max_events,
    )
    return res


@api_router.post("/simulation/stop", tags=["Simulation"])
async def stop_simulation():
    return await simulation_manager.stop()


@api_router.post("/simulation/pause", tags=["Simulation"])
async def pause_simulation():
    return await simulation_manager.pause()


@api_router.post("/simulation/reset", tags=["Simulation"])
async def reset_simulation():
    return await simulation_manager.reset()


@api_router.post("/simulation/inject", tags=["Simulation"])
async def inject_event(event: ActivityEventCreate, db: Session = Depends(get_db)):
    """Allows manual injection of individual events through the live pipeline."""
    payload = await pipeline_service.process_event(db, event.dict())
    return payload


# ---------------------------------------------------------------------------
# 8. Settings — Risk Threshold Persistence
# ---------------------------------------------------------------------------
@api_router.get("/settings/thresholds", tags=["Settings"])
def get_thresholds():
    """Return current risk tier threshold configuration."""
    return threshold_service.get_all()


@api_router.put("/settings/thresholds", tags=["Settings"])
def save_thresholds(body: dict):
    """
    Save new risk tier thresholds.
    Body: { "low_max": int, "medium_max": int, "high_max": int }
    Validation: 0 <= low_max < medium_max < high_max <= 100
    """
    try:
        low_max = int(body.get("low_max", 29))
        medium_max = int(body.get("medium_max", 59))
        high_max = int(body.get("high_max", 79))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Threshold values must be integers.")

    try:
        result = threshold_service.save(low_max, medium_max, high_max)
        return {"status": "saved", "thresholds": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# 9. Admin Block/Unblock
# ---------------------------------------------------------------------------
@api_router.post("/users/{user_id}/block", tags=["Admin"])
def block_user(user_id: str, body: dict = None, db: Session = Depends(get_db)):
    """Block a user account (simulation only). Stores audit trail."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.account_status == "BLOCKED":
        raise HTTPException(status_code=400, detail="User is already blocked")

    body = body or {}
    previous = user.account_status
    user.account_status = "BLOCKED"

    action = AdminAction(
        user_id=user.user_id,
        action="BLOCK",
        performed_by=body.get("performed_by", "admin"),
        reason=body.get("reason", "Manual administrative action"),
        previous_status=previous,
        new_status="BLOCKED",
    )
    db.add(action)
    db.commit()

    return {
        "status": "success",
        "user_id": user_id,
        "account_status": "BLOCKED",
        "action_id": action.id,
    }


@api_router.post("/users/{user_id}/unblock", tags=["Admin"])
def unblock_user(user_id: str, body: dict = None, db: Session = Depends(get_db)):
    """Unblock a user account (simulation only)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.account_status == "ACTIVE":
        raise HTTPException(status_code=400, detail="User is already active")

    body = body or {}
    previous = user.account_status
    user.account_status = "ACTIVE"

    action = AdminAction(
        user_id=user.user_id,
        action="UNBLOCK",
        performed_by=body.get("performed_by", "admin"),
        reason=body.get("reason", "Administrative review completed"),
        previous_status=previous,
        new_status="ACTIVE",
    )
    db.add(action)
    db.commit()

    return {
        "status": "success",
        "user_id": user_id,
        "account_status": "ACTIVE",
        "action_id": action.id,
    }


@api_router.get("/users/{user_id}/admin-actions", tags=["Admin"])
def get_admin_actions(user_id: str, db: Session = Depends(get_db)):
    """Get audit log of block/unblock actions for a user."""
    actions = (
        db.query(AdminAction)
        .filter(AdminAction.user_id == user_id)
        .order_by(AdminAction.timestamp.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "action": a.action,
            "performed_by": a.performed_by,
            "reason": a.reason,
            "previous_status": a.previous_status,
            "new_status": a.new_status,
        }
        for a in actions
    ]


# ---------------------------------------------------------------------------
# 10. WebSocket Stream for Real-Time Event & Risk Updates
# ---------------------------------------------------------------------------
@api_router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await websocket.accept()
    pipeline_service.register_websocket(websocket)
    try:
        # Send initial status
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "simulation": simulation_manager.get_status(),
            "timestamp": datetime.utcnow().isoformat(),
        })
        while True:
            # Keep-alive loop
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pipeline_service.unregister_websocket(websocket)
    except Exception:
        pipeline_service.unregister_websocket(websocket)
