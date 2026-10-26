"""
Real-Time Pipeline Service
==========================
Orchestrates the entire detection flow when an activity event arrives:
  1. Persist Event to SQLite
  2. Load User Profile & Baseline
  3. Extract 58-Feature Vector
  4. Run ML Inference (XGBoost)
  5. Compute Dynamic Risk Score (0-100) & Tier
  6. Compute Local SHAP Explanation & Top Contributing Factors
  7. Persist Updated Risk Score & Risk History
  8. Evaluate & Create Alert if thresholds met
  9. Broadcast Real-time Live Event, Risk Update & Alert to WebSocket clients
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.models import User, ActivityEvent, RiskScore, RiskHistory, Alert
from app.ml.features import extract_user_features
from app.ml.inference import inference_engine
from app.ml.explainability import shap_service
from app.risk.engine import risk_engine
from app.risk.alerts import alert_engine


class PipelineService:
    def __init__(self):
        self.active_websockets = set()

    def register_websocket(self, ws):
        self.active_websockets.add(ws)

    def unregister_websocket(self, ws):
        self.active_websockets.discard(ws)

    async def broadcast_ws(self, message: Dict[str, Any]):
        """Send message to all connected WebSocket clients."""
        dead_sockets = set()
        for ws in list(self.active_websockets):
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.add(ws)
        for dead in dead_sockets:
            self.active_websockets.discard(dead)

    async def process_event(
        self,
        db: Session,
        event_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Processes an incoming activity event through the complete detection pipeline.
        """
        user_id = event_data["user_id"]
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            # Fallback auto-create user
            user = User(
                user_id=user_id,
                name=f"Employee {user_id}",
                department="Engineering",
                role="Software Engineer",
                email=f"{user_id.lower()}@technova.io",
                assigned_pc=event_data.get("pc", "PC-DEFAULT"),
                is_synthetic=True,
                baseline_stats=json.dumps({"logon_mean": 2.0, "logon_std": 0.5}),
            )
            db.add(user)
            db.flush()

        # 1. Persist Activity Event
        event_obj = ActivityEvent(
            event_id=event_data.get("event_id") or f"EVT-{datetime.utcnow().strftime('%H%M%S%f')}",
            timestamp=event_data.get("timestamp") or datetime.utcnow(),
            user_id=user.user_id,
            pc=event_data.get("pc") or user.assigned_pc,
            activity_type=event_data["activity_type"],
            details=json.dumps(event_data.get("details", {})),
            is_after_hours=event_data.get("is_after_hours", False),
            is_weekend=event_data.get("is_weekend", False),
        )
        db.add(event_obj)
        db.flush()

        # 2. Fetch today's recent events for this user
        recent_events = (
            db.query(ActivityEvent)
            .filter(ActivityEvent.user_id == user.user_id)
            .order_by(ActivityEvent.timestamp.desc())
            .limit(50)
            .all()
        )

        # 3. Extract 58-Feature Vector
        features = extract_user_features(user, recent_events, event_obj)

        # 4. ML Inference
        ml_prob, prediction, feature_vector = inference_engine.predict(features)

        # 5. Dynamic Risk Score (0-100) & Tier
        risk_score_val, risk_tier, dev_pts, heur_pts = risk_engine.compute_risk(ml_prob, features)

        # 6. SHAP Local Explanation
        text_explanation, top_factors, base_val = shap_service.explain_instance(feature_vector, top_n=5)

        # 7. Update User's Current Risk Score
        risk_record = db.query(RiskScore).filter(RiskScore.user_id == user.user_id).first()
        if not risk_record:
            risk_record = RiskScore(user_id=user.user_id)
            db.add(risk_record)

        risk_record.current_risk_score = risk_score_val
        risk_record.current_risk_tier = risk_tier
        risk_record.ml_probability = round(ml_prob, 4)
        risk_record.deviation_score = dev_pts
        risk_record.heuristic_score = heur_pts
        risk_record.top_factors = json.dumps(top_factors)
        risk_record.explanation = text_explanation
        risk_record.last_updated = datetime.utcnow()

        # 8. Record Risk History Point
        history_record = RiskHistory(
            user_id=user.user_id,
            timestamp=datetime.utcnow(),
            risk_score=risk_score_val,
            risk_tier=risk_tier,
            ml_probability=round(ml_prob, 4),
            trigger_event_id=event_obj.event_id,
            details=json.dumps({
                "activity_type": event_obj.activity_type,
                "heuristics": heur_pts,
                "deviation": dev_pts
            }),
        )
        db.add(history_record)

        # 9. Evaluate & Create Alert if appropriate
        alert_obj = alert_engine.evaluate_alert(
            user=user,
            risk_score=risk_score_val,
            risk_tier=risk_tier,
            features=features,
            event_activity_type=event_obj.activity_type,
        )
        new_alert_data = None
        if alert_obj:
            db.add(alert_obj)
            db.flush()
            new_alert_data = {
                "id": alert_obj.id,
                "alert_id": alert_obj.alert_id,
                "timestamp": alert_obj.timestamp.isoformat(),
                "user_id": alert_obj.user_id,
                "user_name": user.name,
                "department": user.department,
                "risk_score": alert_obj.risk_score,
                "risk_tier": alert_obj.risk_tier,
                "behavior": alert_obj.behavior,
                "primary_reason": alert_obj.primary_reason,
                "status": alert_obj.status,
            }

        db.commit()

        # 10. Broadcast via WebSocket
        ws_payload = {
            "type": "PIPELINE_UPDATE",
            "event": {
                "id": event_obj.id,
                "event_id": event_obj.event_id,
                "timestamp": event_obj.timestamp.isoformat(),
                "user_id": event_obj.user_id,
                "user_name": user.name,
                "department": user.department,
                "pc": event_obj.pc,
                "activity_type": event_obj.activity_type,
                "details": event_obj.get_details_dict(),
                "is_after_hours": event_obj.is_after_hours,
                "is_weekend": event_obj.is_weekend,
            },
            "risk": {
                "user_id": user.user_id,
                "risk_score": risk_score_val,
                "risk_tier": risk_tier,
                "ml_probability": round(ml_prob, 4),
                "deviation_score": dev_pts,
                "heuristic_score": heur_pts,
                "top_factors": top_factors,
                "explanation": text_explanation,
            },
            "alert": new_alert_data,
        }

        await self.broadcast_ws(ws_payload)

        return ws_payload


pipeline_service = PipelineService()
