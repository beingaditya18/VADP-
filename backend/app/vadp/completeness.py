"""
VADP VADP Completeness Invariant Checker
==============================================

Evaluates the completeness of a Verification Contract by checking
that all nine required provenance components are present and valid.

A contract achieves 'complete' status only when:
  1. Authorization provenance is recorded
  2. Evidence provenance is bound (at least one record)
  3. RAG citations are present
  4. SHAP explainability values are computed
  5. Trust score is calculated
  6. Risk assessment is performed
  7. Digital signature is applied
  8. Merkle inclusion proof is recorded
  9. Human review is completed

This invariant is central to VADP's assurance guarantee:
an incomplete contract cannot be finalized.
"""

from __future__ import annotations

from app.vadp.schemas import CompletenessInvariant


class CompletenessChecker:
    """Evaluates completeness invariant for a Verification Contract."""

    @staticmethod
    def evaluate(
        authorization_result: str | None,
        evidence_count: int,
        rag_citations_count: int,
        shap_values_count: int,
        trust_score: float | None,
        risk_score: float | None,
        digital_signature: str | None,
        merkle_leaf_hash: str | None,
        human_review_status: str,
    ) -> CompletenessInvariant:
        """
        Evaluate all nine completeness criteria and return the invariant.

        Returns a CompletenessInvariant with per-criterion boolean flags,
        an overall_complete flag, and a list of missing component names.
        """
        missing: list[str] = []

        has_authorization = authorization_result is not None and authorization_result != ""
        if not has_authorization:
            missing.append("authorization")

        has_evidence = evidence_count > 0
        if not has_evidence:
            missing.append("evidence")

        has_rag_citations = rag_citations_count > 0
        if not has_rag_citations:
            missing.append("rag_citations")

        has_shap_explanation = shap_values_count > 0
        if not has_shap_explanation:
            missing.append("shap_explanation")

        has_trust_score = trust_score is not None and trust_score > 0.0
        if not has_trust_score:
            missing.append("trust_score")

        has_risk_assessment = risk_score is not None
        if not has_risk_assessment:
            missing.append("risk_assessment")

        has_digital_signature = digital_signature is not None and digital_signature != ""
        if not has_digital_signature:
            missing.append("digital_signature")

        has_merkle_inclusion = merkle_leaf_hash is not None and merkle_leaf_hash != ""
        if not has_merkle_inclusion:
            missing.append("merkle_inclusion")

        has_human_review = human_review_status in (
            "approved",
            "rejected",
            "flagged",
            "override",
        )
        if not has_human_review:
            missing.append("human_review")

        overall_complete = len(missing) == 0

        return CompletenessInvariant(
            has_authorization=has_authorization,
            has_evidence=has_evidence,
            has_rag_citations=has_rag_citations,
            has_shap_explanation=has_shap_explanation,
            has_trust_score=has_trust_score,
            has_risk_assessment=has_risk_assessment,
            has_digital_signature=has_digital_signature,
            has_merkle_inclusion=has_merkle_inclusion,
            has_human_review=has_human_review,
            overall_complete=overall_complete,
            missing_components=missing,
        )

    @staticmethod
    def compute_status(invariant: CompletenessInvariant) -> str:
        """
        Convert completeness invariant to a status string.

        Returns:
          - 'complete' if all criteria are met
          - 'awaiting_review' if only human_review is missing
          - 'awaiting_ledger' if only merkle_inclusion is missing
          - 'incomplete' otherwise
        """
        if invariant.overall_complete:
            return "complete"
        if invariant.missing_components == ["human_review"]:
            return "awaiting_review"
        if invariant.missing_components == ["merkle_inclusion"]:
            return "awaiting_ledger"
        if set(invariant.missing_components) == {"human_review", "merkle_inclusion"}:
            return "awaiting_review_and_ledger"
        return "incomplete"
