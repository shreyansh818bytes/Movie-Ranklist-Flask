"""Tests for authentication helper functions."""

from utils.auth import (
    authenticate_user,
    register_user,
    validate_email,
    validate_password,
)
from utils.models import User, db


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_email(self, app):
        """Test valid email formats."""
        assert validate_email("user@example.com") is True
        assert validate_email("user.name@example.com") is True
        assert validate_email("user+tag@example.com") is True
        assert validate_email("user@subdomain.example.com") is True

    def test_invalid_email(self, app):
        """Test invalid email formats."""
        assert validate_email("") is False
        assert validate_email("userexample.com") is False
        assert validate_email("user@") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@.com") is False
        assert validate_email("user@example") is False


class TestValidatePassword:
    """Tests for password validation."""

    def test_valid_password(self, app):
        """Test valid passwords (8+ characters)."""
        assert validate_password("password") is True
        assert validate_password("12345678") is True
        assert validate_password("a" * 100) is True

    def test_invalid_password(self, app):
        """Test invalid passwords (less than 8 characters)."""
        assert validate_password("") is False
        assert validate_password("1234567") is False
        assert validate_password("short") is False


class TestRegisterUser:
    """Tests for user registration."""

    def test_register_success(self, app):
        """Test successful user registration."""
        with app.app_context():
            user, error = register_user("newuser@example.com", "password123")

            assert error is None
            assert user is not None
            assert user.email == "newuser@example.com"
            assert user.auth_provider == "local"
            assert user.password_hash is not None

    def test_register_email_normalized(self, app):
        """Test that email is normalized to lowercase."""
        with app.app_context():
            user, error = register_user("USER@EXAMPLE.COM", "password123")

            assert error is None
            assert user.email == "user@example.com"

    def test_register_missing_email(self, app):
        """Test registration with missing email."""
        with app.app_context():
            user, error = register_user("", "password123")

            assert user is None
            assert error == "Email and password are required"

    def test_register_missing_password(self, app):
        """Test registration with missing password."""
        with app.app_context():
            user, error = register_user("user@example.com", "")

            assert user is None
            assert error == "Email and password are required"

    def test_register_invalid_email(self, app):
        """Test registration with invalid email format."""
        with app.app_context():
            user, error = register_user("invalidemail", "password123")

            assert user is None
            assert error == "Invalid email format"

    def test_register_short_password(self, app):
        """Test registration with password too short."""
        with app.app_context():
            user, error = register_user("user@example.com", "short")

            assert user is None
            assert error == "Password must be at least 8 characters"

    def test_register_duplicate_email(self, app):
        """Test registration with already registered email."""
        with app.app_context():
            register_user("dupe@example.com", "password123")
            user, error = register_user("dupe@example.com", "different123")

            assert user is None
            assert error == "Email already registered"

    def test_register_duplicate_email_case_insensitive(self, app):
        """Test that duplicate check is case insensitive."""
        with app.app_context():
            register_user("case@example.com", "password123")
            user, error = register_user("CASE@EXAMPLE.COM", "different123")

            assert user is None
            assert error == "Email already registered"


class TestAuthenticateUser:
    """Tests for user authentication."""

    def test_authenticate_success(self, app, sample_user):
        """Test successful authentication."""
        with app.app_context():
            user, error = authenticate_user(
                sample_user["email"], sample_user["password"]
            )

            assert error is None
            assert user is not None
            assert user.email == sample_user["email"]

    def test_authenticate_wrong_password(self, app, sample_user):
        """Test authentication with wrong password."""
        with app.app_context():
            user, error = authenticate_user(sample_user["email"], "wrongpassword")

            assert user is None
            assert error == "Invalid email or password"

    def test_authenticate_nonexistent_user(self, app):
        """Test authentication with non-existent email."""
        with app.app_context():
            user, error = authenticate_user("nonexistent@example.com", "password123")

            assert user is None
            assert error == "Invalid email or password"

    def test_authenticate_missing_email(self, app):
        """Test authentication with missing email."""
        with app.app_context():
            user, error = authenticate_user("", "password123")

            assert user is None
            assert error == "Email and password are required"

    def test_authenticate_missing_password(self, app):
        """Test authentication with missing password."""
        with app.app_context():
            user, error = authenticate_user("user@example.com", "")

            assert user is None
            assert error == "Email and password are required"

    def test_authenticate_case_insensitive_email(self, app, sample_user):
        """Test that authentication is case insensitive for email."""
        with app.app_context():
            user, error = authenticate_user(
                sample_user["email"].upper(), sample_user["password"]
            )

            assert error is None
            assert user is not None

    def test_authenticate_oauth_user(self, app):
        """Test that OAuth users cannot login with password."""
        with app.app_context():
            oauth_user = User(
                email="oauth@example.com",
                password_hash=None,
                auth_provider="google",
                oauth_id="google-123",
            )
            db.session.add(oauth_user)
            db.session.commit()

            user, error = authenticate_user("oauth@example.com", "anypassword")

            assert user is None
            assert error == "Please login with google"
