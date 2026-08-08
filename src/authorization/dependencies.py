"""
VADP Authorization Dependencies
===================================

FastAPI dependencies for Policy Enforcement Point (PEP) checks on routes.
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.authorization.schemas import AccessEvaluationRequest, AuthorizationContextSchema
from app.authorization.service import AuthorizationService
from app.core.exceptions import PolicyViolationError
from app.db.session import get_db_session


def require_permission(resource_type: str, action: str) -> Callable:
    """
    Dependency factory that evaluates access against Policy Engine before allowing execution.

    Usage:
        @router.delete("/cases/{id}", dependencies=[Depends(require_permission("case", "delete"))])
    """

    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session),
    ) -> User:
        service = AuthorizationService(db)
        eval_request = AccessEvaluationRequest(
            resource_type=resource_type,
            action=action,
            context=AuthorizationContextSchema(),
        )

        decision = await service.evaluate_access(current_user, eval_request)
        if not decision.allowed:
            raise PolicyViolationError(
                message=f"Zero Trust Access Denied for action '{action}' on '{resource_type}'. Reason: {decision.reason}"
            )
        return current_user

    return permission_checker
