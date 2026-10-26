"""
Dynamic Risk Scoring Engine
===========================
Calculates a documented, multi-signal 0-100 risk score combining:
  1. ML Classification Probability (45% max weight)
  2. Historical Behavioral Baseline Deviation (25% max weight)
  3. Domain Heuristic Indicators & Multi-Source Signals (30% max weight)

Tiers are dynamically configured via RiskThresholdService.
"""

import numpy as np
from typing import Dict, Any, Tuple
from app.risk.threshold_service import threshold_service


class DynamicRiskEngine:
    """
    Computes a composite, dynamic risk score (0-100) reflecting instantaneous
    and cumulative threat indicators.
    """

    def compute_risk(
        self,
        ml_probability: float,
        features: Dict[str, float],
    ) -> Tuple[int, str, float, float]:
        """
        Calculates composite risk score and tier.

        Parameters:
            ml_probability: Raw ML model output [0.0, 1.0]
            features: Dictionary of extracted user-day features

        Returns:
            risk_score (int): 0-100
            risk_tier (str): LOW, MEDIUM, HIGH, CRITICAL
            deviation_score (float): baseline deviation points [0-25]
            heuristic_score (float): heuristic bonus points [0-30]
        """
        # 1. Base ML Probability Component (0 to 45 points)
        # Using square-root scaling to spread lower-range probabilities
        prob_component = np.sqrt(max(0.0, min(1.0, ml_probability))) * 45.0

        # 2. Behavioral Baseline Deviation Component (0 to 25 points)
        overall_dev = max(0.0, features.get("overall_behavior_deviation", 0.0))
        # Deviation of +3 standard deviations yields full 25 points
        deviation_component = min(25.0, overall_dev * 8.33)

        # 3. Domain Heuristics & Cross-Source Signal Component (0 to 30 points)
        heuristics = 0.0

        # High-risk after-hours exfiltration signals
        if features.get("afterhours_triple_signal", 0.0) > 0:
            heuristics += 20.0
        elif features.get("afterhours_device_and_file", 0.0) > 0:
            heuristics += 15.0
        elif features.get("afterhours_logon_and_device", 0.0) > 0:
            heuristics += 10.0

        # Removable device usage
        if features.get("device_connect_count", 0.0) > 0:
            heuristics += 5.0

        # Bulk file activity
        file_count = features.get("file_access_count", 0.0)
        if file_count >= 15:
            heuristics += 8.0
        elif file_count >= 8:
            heuristics += 4.0

        # Exfiltration via external email
        if features.get("email_external_to", 0.0) > 0:
            heuristics += 4.0
            if features.get("email_with_attachment", 0.0) > 0:
                heuristics += 6.0

        # Multi-PC hopping
        if features.get("multi_pc_logon", 0.0) > 0:
            heuristics += 5.0

        # Cap heuristic component at 30.0
        heuristic_component = min(30.0, heuristics)

        # Total Composite Score (0 - 100)
        raw_score = prob_component + deviation_component + heuristic_component
        final_score = int(np.clip(np.round(raw_score), 0, 100))

        # Determine Tier using dynamic thresholds
        tier = threshold_service.classify_score(final_score)

        return final_score, tier, round(float(deviation_component), 2), round(float(heuristic_component), 2)


risk_engine = DynamicRiskEngine()
