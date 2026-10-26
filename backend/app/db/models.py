"""
SQLAlchemy Database Models
==========================
Defines relational schemas for users, events, risk history, alerts, simulations,
system configuration, and admin audit actions.
Designed to be compatible with both SQLite (for local dev) and PostgreSQL (for prod).
"""

from datetime import datetime
import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    department = Column(String(64), nullable=False, index=True)
    role = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False)
    assigned_pc = Column(String(64), nullable=False)
    is_synthetic = Column(Boolean, default=True)
    baseline_stats = Column(Text, default="{}")  # JSON string of mean/std metrics
    created_at = Column(DateTime, default=datetime.utcnow)

    # Extended profile fields
    manager = Column(String(128), default="")
    location = Column(String(128), default="")
    employment_type = Column(String(32), default="Full-Time")  # Full-Time, Part-Time, Contractor
    join_date = Column(String(32), default="")  # e.g. "2024-03-15"
    normal_hours = Column(String(32), default="09:00–18:00")
    account_status = Column(String(32), default="ACTIVE", index=True)  # ACTIVE, BLOCKED

    # Relationships
    events = relationship("ActivityEvent", back_populates="user", cascade="all, delete-orphan")
    risk_score = relationship("RiskScore", back_populates="user", uselist=False, cascade="all, delete-orphan")
    risk_history = relationship("RiskHistory", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    admin_actions = relationship("AdminAction", back_populates="user", cascade="all, delete-orphan")

    def get_baseline_dict(self):
        try:
            return json.loads(self.baseline_stats or "{}")
        except Exception:
            return {}


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    pc = Column(String(64), nullable=False)
    activity_type = Column(String(64), nullable=False, index=True)  # LOGIN, LOGOUT, DEVICE_CONNECT, etc.
    details = Column(Text, default="{}")  # JSON string for extra data (filename, recipients, etc.)
    is_after_hours = Column(Boolean, default=False)
    is_weekend = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="events")

    __table_args__ = (
        Index("ix_events_user_time", "user_id", "timestamp"),
    )

    def get_details_dict(self):
        try:
            return json.loads(self.details or "{}")
        except Exception:
            return {}


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), unique=True, nullable=False, index=True)
    current_risk_score = Column(Integer, default=10, nullable=False)  # 0 to 100
    current_risk_tier = Column(String(32), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    ml_probability = Column(Float, default=0.0)
    deviation_score = Column(Float, default=0.0)
    heuristic_score = Column(Float, default=0.0)
    top_factors = Column(Text, default="[]")  # JSON array of contributing factors
    explanation = Column(Text, default="Normal baseline behavior observed.")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="risk_score")

    def get_top_factors_list(self):
        try:
            return json.loads(self.top_factors or "[]")
        except Exception:
            return []


class RiskHistory(Base):
    __tablename__ = "risk_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    risk_tier = Column(String(32), nullable=False)
    ml_probability = Column(Float, default=0.0)
    trigger_event_id = Column(String(64), nullable=True)
    details = Column(Text, default="{}")

    # Relationships
    user = relationship("User", back_populates="risk_history")

    __table_args__ = (
        Index("ix_risk_hist_user_time", "user_id", "timestamp"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    risk_tier = Column(String(32), nullable=False)  # HIGH, CRITICAL, MEDIUM
    behavior = Column(String(128), nullable=False)
    primary_reason = Column(Text, nullable=False)
    status = Column(String(32), default="NEW", index=True)  # NEW, ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE
    notes = Column(Text, default="")
    resolved_by = Column(String(128), default="")
    details = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alerts")


class SimulationSession(Base):
    __tablename__ = "simulation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    scenario = Column(String(64), nullable=False)
    status = Column(String(32), default="STOPPED", nullable=False)  # RUNNING, STOPPED, COMPLETED
    events_emitted = Column(Integer, default=0)
    alerts_triggered = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)


class SystemConfig(Base):
    """Persistent key-value configuration store. Single source of truth for risk thresholds."""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(128), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(128), default="system")


class AdminAction(Base):
    """Audit log for admin block/unblock actions."""
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    action = Column(String(32), nullable=False)  # BLOCK, UNBLOCK
    performed_by = Column(String(128), default="admin")
    reason = Column(Text, default="")
    previous_status = Column(String(32), default="")
    new_status = Column(String(32), default="")

    # Relationships
    user = relationship("User", back_populates="admin_actions")
