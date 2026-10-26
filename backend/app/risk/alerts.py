"""
Alert Generation Engine
=======================
Monitors risk score changes and generates actionable security alerts for SOC triage.
"""

import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from app.db.models import Alert, User


class AlertEngine:
    """
    Evaluates newly computed risk scores and triggers alerts when critical thresholds
    or severe anomalous patterns occur.
    """

    def evaluate_alert(
        self,
        user: User,
        risk_score: int,
        risk_tier: str,
        features: Dict[str, float],
        event_activity_type: str,
    ) -> Optional[Alert]:
        """
        Determines whether a new alert should be created based on risk tier and specific behaviors.
        """
        # Only trigger alerts for MEDIUM, HIGH, and CRITICAL
        if risk_tier == "LOW":
            return None

        # Build behavior and primary reason
        reasons = []
        behavior_tags = []

        if features.get("afterhours_triple_signal", 0.0) > 0:
            behavior_tags.append("After-Hours Multi-Signal Exfiltration")
            reasons.append("Simultaneous after-hours logon, USB device insertion, and sensitive file operations detected.")
        elif features.get("afterhours_device_and_file", 0.0) > 0:
            behavior_tags.append("After-Hours USB File Activity")
            reasons.append("Removable drive connected and files copied outside standard business hours.")
        elif features.get("device_connect_count", 0.0) > 0:
            behavior_tags.append("Unusual Removable Storage")
            reasons.append("Removable storage drive connected to workstation.")

        if features.get("file_access_count", 0.0) >= 10:
            behavior_tags.append("High-Volume File Access")
            reasons.append("Unusually high file access and read activity compared to user baseline.")

        if features.get("email_external_to", 0.0) > 0 and features.get("email_with_attachment", 0.0) > 0:
            behavior_tags.append("External Email Data Transfer")
            reasons.append("Email sent to external domain containing attachments.")

        if features.get("overall_behavior_deviation", 0.0) > 2.0:
            behavior_tags.append("Severe Behavioral Deviation")
            reasons.append(f"Overall user activity is +{features.get('overall_behavior_deviation', 0.0):.1f} std devs above baseline.")

        if not behavior_tags:
            behavior_tags.append(f"Elevated AI Risk Score ({risk_score}/100)")
            reasons.append("Model inference probability and heuristic signals exceeded alert threshold.")

        behavior = " | ".join(behavior_tags[:2])
        primary_reason = " ".join(reasons)

        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"

        alert = Alert(
            alert_id=alert_id,
            timestamp=datetime.utcnow(),
            user_id=user.user_id,
            risk_score=risk_score,
            risk_tier=risk_tier,
            behavior=behavior,
            primary_reason=primary_reason,
            status="NEW",
            details=json.dumps({
                "features": {k: round(v, 2) for k, v in features.items() if v > 0},
                "trigger_activity": event_activity_type,
            }),
        )

        return alert


alert_engine = AlertEngine()
