import re

from werkzeug.security import check_password_hash, generate_password_hash

from utils.models import User, db


def validate_email(email):
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password meets minimum requirements."""
    return len(password) >= 8


def register_user(email, password):
    """
    Register a new user with email and password.
    Returns (user, error_message) tuple.
    """
    if not email or not password:
        return None, "Email and password are required"

    if not validate_email(email):
        return None, "Invalid email format"

    if not validate_password(password):
        return None, "Password must be at least 8 characters"

    existing_user = User.query.filter_by(email=email.lower()).first()
    if existing_user:
        return None, "Email already registered"

    user = User(
        email=email.lower(),
        password_hash=generate_password_hash(password),
        auth_provider="local",
    )
    db.session.add(user)
    db.session.commit()

    return user, None


def authenticate_user(email, password):
    """
    Authenticate a user with email and password.
    Returns (user, error_message) tuple.
    """
    if not email or not password:
        return None, "Email and password are required"

    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        return None, "Invalid email or password"

    if user.auth_provider != "local":
        return None, f"Please login with {user.auth_provider}"

    if not user.password_hash or not check_password_hash(user.password_hash, password):
        return None, "Invalid email or password"

    return user, None
