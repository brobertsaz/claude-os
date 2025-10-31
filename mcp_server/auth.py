"""
Simple authentication for Claude OS.
Uses environment variables for credentials - no database needed.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("CLAUDE_OS_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def get_user_credentials() -> dict:
    """
    Get user credentials from environment variables.

    Set in .env or environment:
        CLAUDE_OS_EMAIL=admin@example.com
        CLAUDE_OS_PASSWORD_HASH=<bcrypt hash>

    To generate a password hash:
        python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your_password'))"
    """
    email = os.getenv("CLAUDE_OS_EMAIL")
    password_hash = os.getenv("CLAUDE_OS_PASSWORD_HASH")

    # For development, allow plain password (will be hashed on the fly)
    password_plain = os.getenv("CLAUDE_OS_PASSWORD")

    if not email:
        # Default to disabled auth if not configured
        return None

    if password_hash:
        return {"email": email, "password_hash": password_hash}
    elif password_plain:
        # Hash the plain password (for development only)
        return {"email": email, "password_hash": get_password_hash(password_plain)}
    else:
        return None


def authenticate_user(email: str, password: str) -> bool:
    """Authenticate a user by email and password."""
    creds = get_user_credentials()

    if not creds:
        # Auth disabled
        return False

    if email != creds["email"]:
        return False

    return verify_password(password, creds["password_hash"])


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Dependency to get the current authenticated user.
    Use in FastAPI routes: current_user = Depends(get_current_user)
    """
    creds = get_user_credentials()

    # If auth not configured, allow all requests
    if not creds:
        return {"email": "guest", "auth_disabled": True}

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"email": email}


def is_auth_enabled() -> bool:
    """Check if authentication is enabled."""
    return get_user_credentials() is not None
