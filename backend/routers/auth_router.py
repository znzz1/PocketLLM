"""Authentication API router."""
from fastapi import APIRouter, HTTPException, status
from schemas.auth import LoginRequest, LoginResponse
import utils.dependencies as deps

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    User login endpoint.

    Authenticates user and returns JWT access token.
    """
    deps.monitoring_service.increment_request_count()

    login_response = deps.auth_service.login(request.username, request.password)

    if not login_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return login_response


@router.get("/test")
async def test_auth():
    """Test endpoint to verify auth service is working."""
    return {"message": "Auth service is running", "default_users": ["user1", "admin"]}
