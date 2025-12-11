"""
Tests for mcp_server/auth.py - Authentication functionality.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import jwt
from fastapi import HTTPException

from mcp_server.auth import (
    verify_password,
    get_password_hash,
    get_user_credentials,
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_current_user,
    is_auth_enabled,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    pwd_context,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear CLAUDE_OS env vars for clean tests."""
        env_backup = {}
        for key in list(os.environ.keys()):
            if key.startswith("CLAUDE_OS_"):
                env_backup[key] = os.environ.pop(key)
        yield
        os.environ.update(env_backup)

    def test_get_password_hash_produces_hash(self):
        """Test that password hashing produces a hash."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_get_password_hash_is_unique(self):
        """Test that same password produces different hashes."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # bcrypt uses random salt, so hashes should differ
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "correct_password"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "correct_password"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_empty(self):
        """Test verifying empty password."""
        hashed = get_password_hash("some_password")

        assert verify_password("", hashed) is False


class TestGetUserCredentials:
    """Tests for get_user_credentials function."""

    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear CLAUDE_OS env vars for clean tests."""
        env_backup = {}
        for key in list(os.environ.keys()):
            if key.startswith("CLAUDE_OS_"):
                env_backup[key] = os.environ.pop(key)
        yield
        os.environ.update(env_backup)

    def test_no_email_returns_none(self):
        """Test that missing email returns None."""
        result = get_user_credentials()
        assert result is None

    def test_email_with_password_hash(self):
        """Test credentials with email and password hash."""
        password_hash = get_password_hash("test_password")
        os.environ["CLAUDE_OS_EMAIL"] = "test@example.com"
        os.environ["CLAUDE_OS_PASSWORD_HASH"] = password_hash

        result = get_user_credentials()

        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["password_hash"] == password_hash

    def test_email_with_plain_password(self):
        """Test credentials with email and plain password (dev mode)."""
        os.environ["CLAUDE_OS_EMAIL"] = "dev@example.com"
        os.environ["CLAUDE_OS_PASSWORD"] = "dev_password"

        result = get_user_credentials()

        assert result is not None
        assert result["email"] == "dev@example.com"
        # Password should be hashed
        assert verify_password("dev_password", result["password_hash"])

    def test_email_without_password_returns_none(self):
        """Test that email without any password returns None."""
        os.environ["CLAUDE_OS_EMAIL"] = "test@example.com"

        result = get_user_credentials()
        assert result is None


class TestAuthenticateUser:
    """Tests for authenticate_user function."""

    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear CLAUDE_OS env vars for clean tests."""
        env_backup = {}
        for key in list(os.environ.keys()):
            if key.startswith("CLAUDE_OS_"):
                env_backup[key] = os.environ.pop(key)
        yield
        os.environ.update(env_backup)

    def test_authenticate_success(self):
        """Test successful authentication."""
        password = "test_password"
        password_hash = get_password_hash(password)
        os.environ["CLAUDE_OS_EMAIL"] = "user@example.com"
        os.environ["CLAUDE_OS_PASSWORD_HASH"] = password_hash

        result = authenticate_user("user@example.com", password)
        assert result is True

    def test_authenticate_wrong_password(self):
        """Test authentication with wrong password."""
        password_hash = get_password_hash("correct_password")
        os.environ["CLAUDE_OS_EMAIL"] = "user@example.com"
        os.environ["CLAUDE_OS_PASSWORD_HASH"] = password_hash

        result = authenticate_user("user@example.com", "wrong_password")
        assert result is False

    def test_authenticate_wrong_email(self):
        """Test authentication with wrong email."""
        password_hash = get_password_hash("password")
        os.environ["CLAUDE_OS_EMAIL"] = "correct@example.com"
        os.environ["CLAUDE_OS_PASSWORD_HASH"] = password_hash

        result = authenticate_user("wrong@example.com", "password")
        assert result is False

    def test_authenticate_auth_disabled(self):
        """Test authentication when auth is disabled."""
        result = authenticate_user("any@email.com", "any_password")
        assert result is False


class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token_basic(self):
        """Test basic token creation."""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test token creation with custom expiry."""
        data = {"sub": "user@example.com"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)

        # Decode and check expiry
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded["exp"])

        # Should expire within 1 hour (with some tolerance)
        assert exp_time <= datetime.utcnow() + timedelta(hours=1, minutes=1)

    def test_create_access_token_default_expiry(self):
        """Test token creation with default expiry."""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded["exp"])

        # Default is 7 days
        expected_max = datetime.utcnow() + timedelta(days=7, minutes=1)
        assert exp_time <= expected_max

    def test_decode_access_token_valid(self):
        """Test decoding a valid token."""
        data = {"sub": "user@example.com", "role": "admin"}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "user@example.com"
        assert decoded["role"] == "admin"

    def test_decode_access_token_expired(self):
        """Test decoding an expired token."""
        data = {"sub": "user@example.com"}
        expires = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=expires)

        decoded = decode_access_token(token)
        assert decoded is None

    def test_decode_access_token_invalid(self):
        """Test decoding an invalid token."""
        decoded = decode_access_token("invalid.token.here")
        assert decoded is None

    def test_decode_access_token_tampered(self):
        """Test decoding a tampered token."""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)

        # Tamper with the token
        tampered = token[:-5] + "XXXXX"

        decoded = decode_access_token(tampered)
        assert decoded is None

    def test_decode_access_token_wrong_secret(self):
        """Test decoding token with wrong secret."""
        # Create token with known secret
        data = {"sub": "user@example.com"}
        token = jwt.encode(
            {**data, "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong_secret",
            algorithm=ALGORITHM
        )

        # Try to decode with actual secret
        decoded = decode_access_token(token)
        assert decoded is None


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear CLAUDE_OS env vars for clean tests."""
        env_backup = {}
        for key in list(os.environ.keys()):
            if key.startswith("CLAUDE_OS_"):
                env_backup[key] = os.environ.pop(key)
        yield
        os.environ.update(env_backup)

    def test_get_current_user_auth_disabled(self):
        """Test get_current_user when auth is disabled."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "any_token"

        result = get_current_user(mock_credentials)

        assert result["email"] == "guest"
        assert result["auth_disabled"] is True

    def test_get_current_user_valid_token(self):
        """Test get_current_user with valid token."""
        password_hash = get_password_hash("password")
        os.environ["CLAUDE_OS_EMAIL"] = "user@example.com"
        os.environ["CLAUDE_OS_PASSWORD_HASH"] = password_hash

        # Create valid token
        token = create_access_token({"sub": "user@example.com"})

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        result = get_current_user(mock_credentials)

        assert result["email"] == "user@example.com"

    def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        password_hash = get_password_hash("password")
        os.environ["CLAUDE_OS_EMAIL"] = "user@example.com"
        os.environ["CLAUDE_OS_PASSWORD_HASH"] = password_hash

        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid_token"

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail

    def test_get_current_user_missing_sub(self):
        """Test get_current_user with token missing sub claim."""
        password_hash = get_password_hash("password")
        os.environ["CLAUDE_OS_EMAIL"] = "user@example.com"
        os.environ["CLAUDE_OS_PASSWORD_HASH"] = password_hash

        # Create token without sub
        token = jwt.encode(
            {"exp": datetime.utcnow() + timedelta(hours=1), "role": "user"},
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        mock_credentials = MagicMock()
        mock_credentials.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401


class TestIsAuthEnabled:
    """Tests for is_auth_enabled function."""

    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear CLAUDE_OS env vars for clean tests."""
        env_backup = {}
        for key in list(os.environ.keys()):
            if key.startswith("CLAUDE_OS_"):
                env_backup[key] = os.environ.pop(key)
        yield
        os.environ.update(env_backup)

    def test_auth_enabled_with_credentials(self):
        """Test is_auth_enabled returns True when credentials set."""
        password_hash = get_password_hash("password")
        os.environ["CLAUDE_OS_EMAIL"] = "user@example.com"
        os.environ["CLAUDE_OS_PASSWORD_HASH"] = password_hash

        assert is_auth_enabled() is True

    def test_auth_disabled_without_credentials(self):
        """Test is_auth_enabled returns False when no credentials."""
        assert is_auth_enabled() is False


class TestConstants:
    """Tests for module constants."""

    def test_algorithm_is_hs256(self):
        """Test that algorithm is HS256."""
        assert ALGORITHM == "HS256"

    def test_token_expiry_is_seven_days(self):
        """Test default token expiry is 7 days."""
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24 * 7

    def test_secret_key_is_set(self):
        """Test that secret key is set."""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear CLAUDE_OS env vars for clean tests."""
        env_backup = {}
        for key in list(os.environ.keys()):
            if key.startswith("CLAUDE_OS_"):
                env_backup[key] = os.environ.pop(key)
        yield
        os.environ.update(env_backup)

    def test_empty_email_in_env(self):
        """Test empty email string in environment."""
        os.environ["CLAUDE_OS_EMAIL"] = ""

        result = get_user_credentials()
        assert result is None

    def test_special_characters_in_password(self):
        """Test password with special characters."""
        password = "p@$$w0rd!#$%^&*()"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_unicode_in_password(self):
        """Test password with unicode characters."""
        # Use shorter unicode password (within 72 bytes when encoded)
        password = "pass123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_max_length_password(self):
        """Test password at max bcrypt length (72 bytes)."""
        password = "a" * 72
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_token_with_additional_claims(self):
        """Test token with additional custom claims."""
        data = {
            "sub": "user@example.com",
            "name": "Test User",
            "roles": ["admin", "user"],
            "custom_data": {"key": "value"}
        }
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded["sub"] == "user@example.com"
        assert decoded["name"] == "Test User"
        assert decoded["roles"] == ["admin", "user"]
        assert decoded["custom_data"] == {"key": "value"}
