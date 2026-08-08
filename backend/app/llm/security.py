"""
VADP Prompt Injection & Security Detector
==============================================

Rule-based and pattern-matching security layer detecting adversarial prompt injection attacks:
  - System prompt overrides ("ignore previous instructions", "system prompt", "you are now")
  - Role hijacking & jailbreak patterns ("DAN mode", "developer mode", "unrestricted AI")
  - Data exfiltration attempts
"""

from __future__ import annotations

import re
from typing import NamedTuple

from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityScanResult(NamedTuple):
    is_safe: bool
    risk_score: float
    matched_pattern: str | None
    reason: str | None


class PromptInjectionDetector:
    """Prompt injection & jailbreak detection engine."""

    # Known adversarial prompt injection patterns (case-insensitive regexes)
    INJECTION_PATTERNS = [
        re.compile(
            r"ignore\s+(all\s+)?(previous|above)\s+(instructions|directives|prompts)", re.IGNORECASE
        ),
        re.compile(r"disregard\s+(your\s+)?(system\s+)?prompt", re.IGNORECASE),
        re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
        re.compile(r"\bDAN\s+mode\b", re.IGNORECASE),
        re.compile(r"override\s+(security|safety|trust)\s+(protocols|rules)", re.IGNORECASE),
        re.compile(r"output\s+your\s+entire\s+system\s+prompt", re.IGNORECASE),
        re.compile(r"reveal\s+(secret|internal|confidential)\s+instructions", re.IGNORECASE),
    ]

    @classmethod
    def scan(cls, prompt_text: str) -> SecurityScanResult:
        """
        Scan input prompt text for injection patterns.

        Returns:
            SecurityScanResult(is_safe, risk_score, matched_pattern, reason)
        """
        if not prompt_text or not prompt_text.strip():
            return SecurityScanResult(
                is_safe=True, risk_score=0.0, matched_pattern=None, reason=None
            )

        for pattern in cls.INJECTION_PATTERNS:
            match = pattern.search(prompt_text)
            if match:
                matched_str = match.group(0)
                logger.warning(
                    "Prompt injection detected",
                    extra={"pattern": matched_str, "length": len(prompt_text)},
                )
                return SecurityScanResult(
                    is_safe=False,
                    risk_score=0.95,
                    matched_pattern=matched_str,
                    reason=f"Security Alert: Potential prompt injection pattern detected: '{matched_str}'",
                )

        return SecurityScanResult(is_safe=True, risk_score=0.05, matched_pattern=None, reason=None)
