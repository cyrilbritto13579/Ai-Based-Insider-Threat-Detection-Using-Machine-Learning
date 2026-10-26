"""
Risk Threshold Service
======================
Single source of truth for dynamic risk tier thresholds.
Reads from the SystemConfig DB table and caches in memory.
All components (risk engine, alerts, dashboard) use this service.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from app.db.session import SessionLocal
from app.db.models import SystemConfig


# Default thresholds (used on first run)
DEFAULT_THRESHOLDS = {
    "low_max": 29,
    "medium_max": 59,
    "high_max": 79,
}

THRESHOLD_CONFIG_KEY = "risk_thresholds"


class RiskThresholdService:
    """In-memory cache of risk thresholds backed by persistent DB storage."""

    def __init__(self):
        self._low_max: int = DEFAULT_THRESHOLDS["low_max"]
        self._medium_max: int = DEFAULT_THRESHOLDS["medium_max"]
        self._high_max: int = DEFAULT_THRESHOLDS["high_max"]
        self._last_updated: Optional[str] = None
        self._loaded = False

    def _ensure_loaded(self):
        """Load from DB on first access."""
        if not self._loaded:
            self.load_from_db()

    def load_from_db(self):
        """Read thresholds from the system_config table."""
        try:
            db = SessionLocal()
            try:
                row = db.query(SystemConfig).filter(SystemConfig.key == THRESHOLD_CONFIG_KEY).first()
                if row:
                    data = json.loads(row.value)
                    self._low_max = int(data.get("low_max", DEFAULT_THRESHOLDS["low_max"]))
                    self._medium_max = int(data.get("medium_max", DEFAULT_THRESHOLDS["medium_max"]))
                    self._high_max = int(data.get("high_max", DEFAULT_THRESHOLDS["high_max"]))
                    self._last_updated = row.updated_at.isoformat() if row.updated_at else None
                else:
                    # Seed defaults into DB
                    self._seed_defaults(db)
            finally:
                db.close()
        except Exception as e:
            print(f"Warning: Could not load thresholds from DB: {e}")
        self._loaded = True

    def _seed_defaults(self, db):
        """Insert default thresholds into DB."""
        row = SystemConfig(
            key=THRESHOLD_CONFIG_KEY,
            value=json.dumps(DEFAULT_THRESHOLDS),
            updated_by="system",
        )
        db.add(row)
        db.commit()
        self._last_updated = datetime.utcnow().isoformat()

    @property
    def low_max(self) -> int:
        self._ensure_loaded()
        return self._low_max

    @property
    def medium_max(self) -> int:
        self._ensure_loaded()
        return self._medium_max

    @property
    def high_max(self) -> int:
        self._ensure_loaded()
        return self._high_max

    @property
    def critical_min(self) -> int:
        self._ensure_loaded()
        return self._high_max + 1

    @property
    def last_updated(self) -> Optional[str]:
        self._ensure_loaded()
        return self._last_updated

    def get_all(self) -> Dict[str, Any]:
        """Return current threshold configuration."""
        self._ensure_loaded()
        return {
            "low_max": self._low_max,
            "medium_max": self._medium_max,
            "high_max": self._high_max,
            "critical_min": self._high_max + 1,
            "last_updated": self._last_updated,
        }

    def classify_score(self, score: int) -> str:
        """Classify a 0-100 risk score into a tier using current thresholds."""
        self._ensure_loaded()
        if score <= self._low_max:
            return "LOW"
        elif score <= self._medium_max:
            return "MEDIUM"
        elif score <= self._high_max:
            return "HIGH"
        else:
            return "CRITICAL"

    def save(self, low_max: int, medium_max: int, high_max: int) -> Dict[str, Any]:
        """
        Validate and persist new thresholds.
        Raises ValueError if validation fails.
        """
        # Validation: 0 <= low_max < medium_max < high_max <= 100
        if not (0 <= low_max < medium_max < high_max <= 100):
            raise ValueError(
                f"Invalid thresholds: must satisfy 0 <= low_max ({low_max}) < "
                f"medium_max ({medium_max}) < high_max ({high_max}) <= 100"
            )

        db = SessionLocal()
        try:
            row = db.query(SystemConfig).filter(SystemConfig.key == THRESHOLD_CONFIG_KEY).first()
            data = json.dumps({
                "low_max": low_max,
                "medium_max": medium_max,
                "high_max": high_max,
            })
            if row:
                row.value = data
                row.updated_at = datetime.utcnow()
                row.updated_by = "admin"
            else:
                row = SystemConfig(
                    key=THRESHOLD_CONFIG_KEY,
                    value=data,
                    updated_by="admin",
                )
                db.add(row)
            db.commit()

            # Update in-memory cache
            self._low_max = low_max
            self._medium_max = medium_max
            self._high_max = high_max
            self._last_updated = datetime.utcnow().isoformat()

            return self.get_all()
        finally:
            db.close()


# Module-level singleton — import this everywhere
threshold_service = RiskThresholdService()
