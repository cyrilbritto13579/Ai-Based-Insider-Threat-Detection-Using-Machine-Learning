"""
Application Configuration
=========================
Core settings for Insider Threat Detection V2 backend.
"""

import os
from pydantic import BaseModel
from typing import List


class Settings(BaseModel):
    PROJECT_NAME: str = "TraceGuard AI"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Base paths
    PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
    ARTIFACTS_DIR: str = os.path.join(DATA_DIR, "artifacts")
    PROCESSED_DIR: str = os.path.join(DATA_DIR, "processed")
    
    # SQLite Database
    DATABASE_URL: str = f"sqlite:///{os.path.join(DATA_DIR, 'insider_threat_v2.db')}"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    # Working hours definition
    WORK_HOUR_START: int = 7
    WORK_HOUR_END: int = 18
    
    # Risk Tier Thresholds
    RISK_TIER_LOW_MAX: int = 29
    RISK_TIER_MEDIUM_MAX: int = 59
    RISK_TIER_HIGH_MAX: int = 79
    RISK_TIER_CRITICAL_MIN: int = 80
    
    # ML Model Paths
    MODEL_PATH: str = os.path.join(ARTIFACTS_DIR, "best_model.joblib")
    METADATA_PATH: str = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
    COMPARISON_PATH: str = os.path.join(ARTIFACTS_DIR, "model_comparison.json")
    FEATURE_SCHEMA_PATH: str = os.path.join(ARTIFACTS_DIR, "feature_schema.json")
    SHAP_IMPORTANCE_PATH: str = os.path.join(ARTIFACTS_DIR, "shap_global_importance.json")


settings = Settings()
