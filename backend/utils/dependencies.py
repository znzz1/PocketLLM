"""FastAPI dependencies for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from schemas.auth import TokenPayload

# Global service instances (will be initialized in main.py)
auth_service = None
session_service = None
cache_manager = None
inference_service = None
monitoring_service = None

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> TokenPayload:
    """Verify JWT token and return user info."""
    token = credentials.credentials
    token_data = auth_service.verify_token(token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def get_current_admin(
    current_user: Annotated[TokenPayload, Depends(get_current_user)]
) -> TokenPayload:
    """Verify that current user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
