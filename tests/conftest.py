import pytest

from app import app as flask_app
from utils.models import User, db


@pytest.fixture
def app():
    """Create application for testing."""
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-key",
        }
    )

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    from werkzeug.security import generate_password_hash

    with app.app_context():
        user = User(
            email="test@example.com",
            password_hash=generate_password_hash("password123"),
            auth_provider="local",
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        user_email = user.email
    return {"id": user_id, "email": user_email, "password": "password123"}
