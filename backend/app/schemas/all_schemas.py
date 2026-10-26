"""
Pydantic Schemas for Users, Events, Risk, Alerts, Analytics, and Simulation
===========================================================================
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# User Schemas
# ---------------------------------------------------------------------------
class UserBase(BaseModel):
    user_id: str
    name: str
    department: str
    role: str
    email: str
    assigned_pc: str
    is_synthetic: bool = True


class UserResponse(UserBase):
    id: int
    current_risk_score: int = 10
    current_risk_tier: str = "LOW"
    ml_probability: float = 0.0
    last_updated: Optional[datetime] = None
    manager: str = ""
    location: str = ""
    employment_type: str = "Full-Time"
    join_date: str = ""
    normal_hours: str = "09:00–18:00"
    account_status: str = "ACTIVE"

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    baseline_stats: Dict[str, Any] = {}
    explanation: str = "Normal baseline behavior observed."
    top_factors: List[Dict[str, Any]] = []
    recent_events_count: int = 0
    total_alerts_count: int = 0
    login_count: int = 0
    device_count: int = 0
    file_count: int = 0
    email_count: int = 0
    last_activity: Optional[str] = None


# ---------------------------------------------------------------------------
# Event Schemas
# ---------------------------------------------------------------------------
class ActivityEventCreate(BaseModel):
    user_id: str
    pc: Optional[str] = None
    activity_type: str  # LOGIN, LOGOUT, DEVICE_CONNECT, DEVICE_DISCONNECT, FILE_ACCESS, FILE_COPY, EMAIL_ACTIVITY
    timestamp: Optional[datetime] = None
    details: Dict[str, Any] = {}


class ActivityEventResponse(BaseModel):
    id: int
    event_id: str
    timestamp: datetime
    user_id: str
    pc: str
    activity_type: str
    details: Dict[str, Any] = {}
    is_after_hours: bool = False
    is_weekend: bool = False

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Risk Schemas
# ---------------------------------------------------------------------------
class RiskScoreResponse(BaseModel):
    user_id: str
    current_risk_score: int
    current_risk_tier: str
    ml_probability: float
    deviation_score: float
    heuristic_score: float
    top_factors: List[Dict[str, Any]] = []
    explanation: str
    last_updated: datetime

    class Config:
        from_attributes = True


class RiskHistoryPoint(BaseModel):
    timestamp: datetime
    risk_score: int
    risk_tier: str
    ml_probability: float

    class Config:
        from_attributes = True


class RiskOverviewResponse(BaseModel):
    total_monitored_users: int
    total_events_analyzed: int
    suspicious_users_count: int
    critical_alerts_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    open_alerts_count: int = 0
    tier_distribution: Dict[str, int]
    system_health: Dict[str, str]


# ---------------------------------------------------------------------------
# Alert Schemas
# ---------------------------------------------------------------------------
class AlertResponse(BaseModel):
    id: int
    alert_id: str
    timestamp: datetime
    user_id: str
    user_name: Optional[str] = None
    department: Optional[str] = None
    risk_score: int
    risk_tier: str
    behavior: str
    primary_reason: str
    status: str
    notes: str = ""
    resolved_by: str = ""
    details: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class AlertAcknowledgeRequest(BaseModel):
    status: str = "ACKNOWLEDGED"  # ACKNOWLEDGED, INVESTIGATING, RESOLVED, FALSE_POSITIVE
    notes: Optional[str] = None
    resolved_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Simulation Schemas
# ---------------------------------------------------------------------------
class SimulationStatusResponse(BaseModel):
    status: str  # RUNNING, STOPPED, PAUSED, IDLE
    current_scenario: Optional[str] = None
    target_user_id: Optional[str] = None
    events_emitted: int = 0
    alerts_triggered: int = 0
    interval_seconds: float = 1.5
    available_scenarios: List[Dict[str, str]] = []


class SimulationStartRequest(BaseModel):
    scenario: str  # NORMAL_EMPLOYEE, AFTER_HOURS, UNUSUAL_DEVICE_ACTIVITY, UNUSUAL_FILE_ACTIVITY, SUSPICIOUS_DATA_COLLECTION, MULTI_SIGNAL_ANOMALY
    target_user_id: Optional[str] = None
    speed_interval: float = 1.0  # seconds per event
    max_events: Optional[int] = 50


# ---------------------------------------------------------------------------
# Analytics & Model Schemas
# ---------------------------------------------------------------------------
class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    category: str


class ModelMetricsResponse(BaseModel):
    best_model_name: str
    best_model_type: str
    optimal_threshold: float
    validation_metrics: Dict[str, Any]
    test_metrics: Dict[str, Any]
    comparison_table: List[Dict[str, Any]]
    dataset_summary: Dict[str, Any]


class ShapExplanationResponse(BaseModel):
    user_id: str
    risk_score: int
    risk_tier: str
    ml_probability: float
    text_explanation: str
    top_factors: List[Dict[str, Any]]
    base_value: float = 0.0
