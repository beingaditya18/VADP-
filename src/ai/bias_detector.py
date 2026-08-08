"""
VADP Bias & Fairness Detector
===================================

Scans AI judicial recommendations for potential jurisdictional, demographic, socio-economic, or procedural bias.
"""

from __future__ import annotations

import re


class BiasDetector:
    """Bias & Fairness Audit Engine."""

    BIAS_KEYWORDS = [
        r"\b(religion|caste|gender|socio-economic\s+class)\b",
        r"\b(unfavorable\s+background|slum\ resident)\b",
        r"\b(stereotype|inherent\ bias)\b",
    ]

    @classmethod
    def detect_bias(cls, recommendation_text: str) -> list[str]:
        """
        Scan text for bias markers. Returns list of detected bias flags (empty if clean).
        """
        if not recommendation_text:
            return []

        bias_flags = []
        for pattern_str in cls.BIAS_KEYWORDS:
            if re.search(pattern_str, recommendation_text, re.IGNORECASE):
                bias_flags.append(f"Potential Bias Marker Detected: '{pattern_str}'")

        return bias_flags
