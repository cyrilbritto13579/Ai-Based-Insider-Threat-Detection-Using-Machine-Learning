"""
ML Inference Engine
===================
Loads the trained model pipeline and runs prediction on extracted feature vectors.
"""

import os
import json
import joblib
import numpy as np
from typing import Dict, Any, Tuple
from app.core.config import settings


class MLInferenceEngine:
    def __init__(self):
        self.model = None
        self.feature_schema = []
        self.optimal_threshold = 0.1184
        self.metadata = {}
        self._load_artifacts()

    def _load_artifacts(self):
        """Load trained XGBoost model and feature schema."""
        if os.path.exists(settings.MODEL_PATH):
            try:
                self.model = joblib.load(settings.MODEL_PATH)
            except Exception as e:
                print(f"Warning: Could not load model from {settings.MODEL_PATH}: {e}")

        if os.path.exists(settings.FEATURE_SCHEMA_PATH):
            try:
                with open(settings.FEATURE_SCHEMA_PATH, "r") as f:
                    schema_data = json.load(f)
                    self.feature_schema = schema_data.get("feature_columns", [])
            except Exception as e:
                print(f"Warning: Could not load feature schema: {e}")

        if os.path.exists(settings.METADATA_PATH):
            try:
                with open(settings.METADATA_PATH, "r") as f:
                    self.metadata = json.load(f)
                    self.optimal_threshold = self.metadata.get("optimal_threshold", 0.1184)
            except Exception as e:
                print(f"Warning: Could not load metadata: {e}")

    def predict(self, feature_dict: Dict[str, float]) -> Tuple[float, int, np.ndarray]:
        """
        Run inference on feature dictionary.
        
        Returns:
            probability (float): Raw positive class probability [0.0, 1.0]
            prediction (int): Binary prediction using optimal threshold (0 or 1)
            feature_vector (np.ndarray): 1D array of ordered features
        """
        if not self.feature_schema:
            self._load_artifacts()

        # Build ordered vector
        vector = []
        for feat in self.feature_schema:
            val = feature_dict.get(feat, 0.0)
            vector.append(float(val))

        X = np.array([vector], dtype=np.float32)
        np.nan_to_num(X, copy=False, nan=0.0, posinf=0.0, neginf=0.0)

        if self.model is not None and hasattr(self.model, "predict_proba"):
            try:
                probs = self.model.predict_proba(X)
                prob = float(probs[0, 1]) if probs.shape[1] > 1 else float(probs[0, 0])
            except Exception as e:
                print(f"Inference error: {e}")
                prob = 0.05
        else:
            # Fallback heuristic if model not loaded
            prob = 0.05

        prediction = 1 if prob >= self.optimal_threshold else 0
        return prob, prediction, X[0]


inference_engine = MLInferenceEngine()
