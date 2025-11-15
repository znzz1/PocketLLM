"""Authentication service for user management and JWT token generation."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from schemas.auth import User, TokenPayload, LoginResponse
from config import settings
import uuid


class AuthService:
    """Handles user authentication and JWT token management."""

    def __init__(self):
        """Initialize authentication service."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # In-memory user store (replace with database in production)
        self.users: dict[str, User] = {}
        self._initialize_default_users()

    def _initialize_default_users(self):
        """Create default users for development."""
        # Default regular user
        self.users["user1"] = User(
            user_id=str(uuid.uuid4()),
            username="user1",
            password_hash=self.get_password_hash("password123"),
            is_admin=False
        )
        # Default admin user
        self.users["admin"] = User(
            user_id=str(uuid.uuid4()),
            username="admin",
            password_hash=self.get_password_hash("admin123"),
            is_admin=True
        )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = self.users.get(username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(self, user: User) -> str:
        """Create JWT access token for authenticated user."""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = TokenPayload(
            sub=user.user_id,
            username=user.username,
            is_admin=user.is_admin,
            exp=int(expire.timestamp())
        )
        token = jwt.encode(
            payload.model_dump(),
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return token

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            return token_data
        except JWTError:
            return None

    def login(self, username: str, password: str) -> Optional[LoginResponse]:
        """Process user login and return access token."""
        user = self.authenticate_user(username, password)
        if not user:
            return None

        access_token = self.create_access_token(user)
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id,
            username=user.username,
            is_admin=user.is_admin
        )

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id."""
        for user in self.users.values():
            if user.user_id == user_id:
                return user
        return None
