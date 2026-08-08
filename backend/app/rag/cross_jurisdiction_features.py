"""
Cross-Jurisdictional Domain-Specific Statutory Feature Extraction
==================================================================

Extracts jurisdiction-tailored statutory and citation features for:
1. Indian Judicial System (BSA §63(4), Evidence Act §65B, IPC, CrPC)
2. US Supreme Court (SCOTUS): US Code (28 U.S.C., 42 U.S.C.), FRE 902/1002, Constitutional Amendments
3. European Court of Human Rights (ECtHR): ECHR Articles (Art 6, Art 8, Art 10, Art 13, Strasbourg precedence)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set
from pydantic import BaseModel


class JurisdictionFeatures(BaseModel):
    jurisdiction: str
    statutory_alignment_score: float
    citation_depth_score: float
    procedural_rule_score: float
    constitutional_clause_score: float


class CrossJurisdictionFeatureExtractor:
    """Extracts jurisdiction-specific statutory features for GBT LambdaMART re-ranking."""

    # US SCOTUS Statutory & Procedural Patterns
    US_CODE_PATTERN = re.compile(r"\b\d+\s+u\.?s\.?c\.?\s+§?\s*\d+\b", re.IGNORECASE)
    US_FRE_PATTERN = re.compile(r"\bfre\s+\d+|fed\.?\s+r\.?\037evid\.?\s+\d+|rule\s+\d+\b", re.IGNORECASE)
    US_CONST_PATTERN = re.compile(r"\b(first|fourth|fifth|sixth|fourteenth)\s+amendment|due\037process|equal\037protection\b", re.IGNORECASE)

    # EU ECtHR Statutory & Convention Patterns
    EU_ECHR_ARTICLE_PATTERN = re.compile(r"\barticle\s+(6|8|10|13|14|41|34)\b|\bechr\b", re.IGNORECASE)
    EU_STRASBOURG_PATTERN = re.compile(r"\bstrasbourg|margin\s+of\s+appreciation|fair\s+trial|proportionality\b", re.IGNORECASE)

    # Indian Statutory Patterns
    IN_BSA_PATTERN = re.compile(r"\bsection\s+65b|bsa\s+63|electronic\s+record|certificate\b", re.IGNORECASE)

    @classmethod
    def extract_us_scotus_features(cls, query_text: str, chunk_content: str) -> JurisdictionFeatures:
        """Extract statutory features for US Supreme Court corpus."""
        q_lower = query_text.lower()
        c_lower = chunk_content.lower()

        us_code_q = bool(cls.US_CODE_PATTERN.search(q_lower))
        us_code_c = bool(cls.US_CODE_PATTERN.search(c_lower))
        code_score = 1.0 if (us_code_q and us_code_c) else (0.5 if us_code_c else 0.1)

        fre_c = bool(cls.US_FRE_PATTERN.search(c_lower))
        fre_score = 1.0 if fre_c else 0.2

        const_c = bool(cls.US_CONST_PATTERN.search(c_lower))
        const_score = 1.0 if const_c else 0.3

        stat_align = round((code_score + fre_score + const_score) / 3.0, 4)

        return JurisdictionFeatures(
            jurisdiction="US_SCOTUS",
            statutory_alignment_score=stat_align,
            citation_depth_score=round(code_score, 4),
            procedural_rule_score=round(fre_score, 4),
            constitutional_clause_score=round(const_score, 4),
        )

    @classmethod
    def extract_eu_ecthr_features(cls, query_text: str, chunk_content: str) -> JurisdictionFeatures:
        """Extract statutory features for ECtHR European legal corpus."""
        q_lower = query_text.lower()
        c_lower = chunk_content.lower()

        echr_q = bool(cls.EU_ECHR_ARTICLE_PATTERN.search(q_lower))
        echr_c = bool(cls.EU_ECHR_ARTICLE_PATTERN.search(c_lower))
        echr_score = 1.0 if (echr_q and echr_c) else (0.6 if echr_c else 0.15)

        strasbourg_c = bool(cls.EU_STRASBOURG_PATTERN.search(c_lower))
        strasbourg_score = 1.0 if strasbourg_c else 0.25

        stat_align = round((echr_score * 0.6 + strasbourg_score * 0.4), 4)

        return JurisdictionFeatures(
            jurisdiction="EU_ECtHR",
            statutory_alignment_score=stat_align,
            citation_depth_score=round(echr_score, 4),
            procedural_rule_score=round(strasbourg_score, 4),
            constitutional_clause_score=round(echr_score, 4),
        )
