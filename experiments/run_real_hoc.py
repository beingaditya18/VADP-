"""
Real Empirical Human Override Coverage (HOC) Calculation Engine
===============================================================

Evaluates real Trust Scores computed by the VADP Trust Scoring Engine
(app/ai/trust_engine.py) across database cases under Algorithm 5 escalation thresholds:
  - Trust threshold: tau_p = 0.88
  - Risk threshold: tau_sigma = 0.12

Calculates true empirical HOC percentage, 95% Wilson score confidence interval,
and domain category breakdowns.
Saves results to backend/evaluation/REAL_HOC_RESULTS.json.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.trust_engine import TrustScoringEngine
from app.cases.models import Case
from app.db.init_db import init_db
from app.db.session import get_session_factory
from app.vadp.models import VerificationContract

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_real_hoc")


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson score interval for binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996  # 95% confidence
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return (round(max(0.0, center - spread) * 100, 2), round(min(1.0, center + spread) * 100, 2))


async def run_real_hoc_calculation(tau_p: float = 0.88, tau_sigma: float = 0.12) -> dict:
    logger.info("==========================================================")
    logger.info("  REAL HOC CALCULATION VIA TRUST SCORING ENGINE")
    logger.info("==========================================================")
    await init_db()

    session_factory = get_session_factory()
    async with session_factory() as db:
        query = select(VerificationContract, Case.case_type).join(Case, VerificationContract.case_id == Case.id)
        res = await db.execute(query)
        rows = res.all()

        if not rows:
            logger.error("No Verification Contracts found in database!")
            return {}

        total_contracts = len(rows)
        logger.info(f"Loaded {total_contracts} Verification Contracts with Trust Scores...")

        category_stats: dict[str, dict] = {}
        escalated_count = 0
        approved_count = 0

        for contract, category in rows:
            if category not in category_stats:
                category_stats[category] = {"total": 0, "escalated": 0, "approved": 0}

            category_stats[category]["total"] += 1

            # Recalculate or inspect Trust Score from contract & Algorithm 5 predicate
            t_score = contract.trust_score
            r_score = contract.risk_score

            # Algorithm 5: Escalate if Trust < tau_p OR Risk > tau_sigma
            is_escalated = (t_score < tau_p) or (r_score > tau_sigma) or (contract.human_review_status in ["pending_review", "mandatory_human_review", "flagged"])

            if is_escalated:
                escalated_count += 1
                category_stats[category]["escalated"] += 1
            else:
                approved_count += 1
                category_stats[category]["approved"] += 1

        hoc_rate = round((escalated_count / total_contracts) * 100, 2)
        ci_low, ci_high = wilson_ci(escalated_count, total_contracts)

        logger.info("==========================================================")
        logger.info(f"  REAL HOC EMPIRICAL METRICS (N = {total_contracts})")
        logger.info("==========================================================")
        logger.info(f"  - Total Evaluated Contracts : {total_contracts}")
        logger.info(f"  - Escalated (Human Review)  : {escalated_count}")
        logger.info(f"  - Auto-Approved            : {approved_count}")
        logger.info(f"  - Calculated HOC            : {hoc_rate}% (95% CI: [{ci_low}%, {ci_high}%])")
        logger.info(f"  - Escalation Tau_p (Trust)  : {tau_p}")
        logger.info(f"  - Escalation Tau_sigma (Risk): {tau_sigma}")
        logger.info("==========================================================\n")

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        results = {
            "calculated_at": now_str,
            "total_contracts": total_contracts,
            "escalated_count": escalated_count,
            "approved_count": approved_count,
            "hoc_percentage": hoc_rate,
            "ci_95": [ci_low, ci_high],
            "tau_p": tau_p,
            "tau_sigma": tau_sigma,
            "category_breakdown": category_stats,
        }

        out_json = BACKEND_DIR / "evaluation" / "REAL_HOC_RESULTS.json"
        out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
        logger.info(f"Saved real HOC calculation results to {out_json}")

        return results


if __name__ == "__main__":
    asyncio.run(run_real_hoc_calculation())
