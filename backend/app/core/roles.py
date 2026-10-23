from enum import Enum
from typing import Callable
from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user


class Role(str, Enum):
    NATIONAL_OFFICER = "NATIONAL_OFFICER"
    REGIONAL_OFFICER = "REGIONAL_OFFICER"
    RULES_OWNER = "RULES_OWNER"
    RULES_APPROVER = "RULES_APPROVER"
    COLLEGE_ADMIN = "COLLEGE_ADMIN"
    STUDENT = "STUDENT"
    EMPLOYER = "EMPLOYER"
    AUDITOR = "AUDITOR"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"


OFFICER_ROLES = {Role.NATIONAL_OFFICER, Role.REGIONAL_OFFICER}
ALL_ROLES = set(Role)


def require_role(*roles: Role) -> Callable:
    """FastAPI dependency: raises 403 if current user's role is not in `roles`."""
    allowed = set(roles)

    def _check(current_user=Depends(get_current_user)):
        if Role(current_user["role"]) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "You do not have access to this."},
            )
        return current_user

    return _check


def require_any_role(current_user=Depends(get_current_user)):
    """Dependency that allows any authenticated user."""
    return current_user
