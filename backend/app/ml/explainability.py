"""
Explainable AI (XAI) Module using SHAP
======================================
Computes exact local SHAP values on individual feature vectors and translates
them into clear, defensive security analyst rationales.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from app.ml.inference import inference_engine

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


class SHAPExplainerService:
    def __init__(self):
        self.explainer = None
        self._init_explainer()

    def _init_explainer(self):
        """Initialize TreeExplainer from the loaded XGBoost model."""
        if HAS_SHAP and inference_engine.model is not None:
            try:
                self.explainer = shap.TreeExplainer(inference_engine.model)
            except Exception as e:
                print(f"Warning: Could not initialize TreeExplainer: {e}")

    def explain_instance(self, feature_vector: np.ndarray, top_n: int = 5) -> Tuple[str, List[Dict[str, Any]], float]:
        """
        Explain a single feature vector using SHAP.

        Returns:
            explanation_text (str): Human-readable natural language justification
            top_factors (list): Ordered list of top contributing features
            base_value (float): SHAP baseline value
        """
        if not HAS_SHAP or self.explainer is None:
            self._init_explainer()

        feature_names = inference_engine.feature_schema
        if len(feature_vector) != len(feature_names):
            return "Normal activity; insufficient feature context for explanation.", [], 0.0

        impacts = []
        base_value = 0.0

        if HAS_SHAP and self.explainer is not None:
            try:
                X_2d = np.array([feature_vector], dtype=np.float32)
                shap_obj = self.explainer(X_2d)
                vals = shap_obj.values[0]

                # If binary class, take positive class (index 1)
                if len(vals.shape) > 1 and vals.shape[1] == 2:
                    vals = vals[:, 1]

                if hasattr(shap_obj, "base_values"):
                    bv = shap_obj.base_values[0]
                    base_value = float(bv[1] if isinstance(bv, (list, np.ndarray)) and len(bv) > 1 else bv)

                for i, name in enumerate(feature_names):
                    impacts.append({
                        "feature": name,
                        "value": round(float(feature_vector[i]), 2),
                        "impact_score": round(float(vals[i]), 4),
                        "direction": "Pushes Risk UP" if vals[i] > 0 else "Pushes Risk DOWN"
                    })

                # Sort by absolute SHAP impact
                impacts.sort(key=lambda x: abs(x["impact_score"]), reverse=True)
            except Exception as e:
                print(f"SHAP compute error: {e}")

        # If SHAP failed or returned empty, create heuristic impact ranking
        if not impacts:
            for i, name in enumerate(feature_names):
                val = float(feature_vector[i])
                if val > 0:
                    impacts.append({
                        "feature": name,
                        "value": round(val, 2),
                        "impact_score": round(val * 0.1, 4),
                        "direction": "Pushes Risk UP"
                    })
            impacts.sort(key=lambda x: x["value"], reverse=True)

        top_factors = impacts[:top_n]
        text_explanation = self._generate_security_rationale(top_factors)
        return text_explanation, top_factors, base_value

    def _generate_security_rationale(self, top_factors: List[Dict[str, Any]]) -> str:
        """
        Translates raw feature contributions into compliant, non-accusatory security language.
        Rules:
          - Never say "This employee is malicious"
          - Use "Suspicious behavior detected; investigation recommended."
        """
        risk_raisers = [f for f in top_factors if f["impact_score"] > 0.05]
        risk_lowerers = [f for f in top_factors if f["impact_score"] < -0.05]

        if not risk_raisers and not risk_lowerers:
            return "Observed activity aligns closely with the user's historical baseline profile. No critical anomalies detected."

        points = []
        if risk_raisers:
            points.append("Suspicious behavioral indicators detected requiring SOC analyst review:")
            for item in risk_raisers:
                f_name = item["feature"].replace("_", " ").title()
                val = item["value"]
                points.append(f"  • {f_name} (Observed: {val}, Impact: +{item['impact_score']:.3f})")

        if risk_lowerers:
            points.append("\nMitigating behavioral baselines:")
            for item in risk_lowerers:
                f_name = item["feature"].replace("_", " ").title()
                val = item["value"]
                points.append(f"  • {f_name} (Normal baseline offset: {item['impact_score']:.3f})")

        points.append("\nSummary: Anomalous deviation from typical employee patterns observed; investigation recommended.")
        return "\n".join(points)


shap_service = SHAPExplainerService()
