"""Tests for database models."""

from werkzeug.security import generate_password_hash

from utils.models import User, db


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app):
        """Test creating a user with required fields."""
        with app.app_context():
            user = User(
                email="newuser@example.com",
                password_hash=generate_password_hash("testpass"),
                auth_provider="local",
            )
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.email == "newuser@example.com"
            assert user.auth_provider == "local"
            assert user.created_at is not None

    def test_user_email_unique(self, app):
        """Test that email must be unique."""
        import sqlalchemy

        with app.app_context():
            user1 = User(email="same@example.com", password_hash="hash1")
            db.session.add(user1)
            db.session.commit()

            user2 = User(email="same@example.com", password_hash="hash2")
            db.session.add(user2)

            try:
                db.session.commit()
                assert False, "Should have raised IntegrityError"
            except sqlalchemy.exc.IntegrityError:
                db.session.rollback()

    def test_user_to_dict(self, app):
        """Test the to_dict method returns correct data."""
        with app.app_context():
            user = User(
                email="dicttest@example.com",
                password_hash="somehash",
                auth_provider="local",
            )
            db.session.add(user)
            db.session.commit()

            user_dict = user.to_dict()
            assert "id" in user_dict
            assert user_dict["email"] == "dicttest@example.com"
            assert user_dict["username"] == "dicttest"
            assert user_dict["auth_provider"] == "local"
            assert "password_hash" not in user_dict

    def test_user_default_auth_provider(self, app):
        """Test that auth_provider defaults to 'local'."""
        with app.app_context():
            user = User(email="default@example.com", password_hash="hash")
            db.session.add(user)
            db.session.commit()

            assert user.auth_provider == "local"

    def test_user_oauth_fields_nullable(self, app):
        """Test that OAuth fields can be null for local users."""
        with app.app_context():
            user = User(
                email="localuser@example.com",
                password_hash="hash",
                auth_provider="local",
            )
            db.session.add(user)
            db.session.commit()

            assert user.oauth_id is None
            assert user.password_hash == "hash"

    def test_user_oauth_user_no_password(self, app):
        """Test that OAuth users can have null password_hash."""
        with app.app_context():
            user = User(
                email="oauthuser@example.com",
                password_hash=None,
                auth_provider="google",
                oauth_id="google-oauth-id-123",
            )
            db.session.add(user)
            db.session.commit()

            assert user.password_hash is None
            assert user.oauth_id == "google-oauth-id-123"
            assert user.auth_provider == "google"

    def test_user_is_authenticated(self, app):
        """Test that User model has Flask-Login UserMixin methods."""
        with app.app_context():
            user = User(email="authed@example.com", password_hash="hash")
            db.session.add(user)
            db.session.commit()

            assert user.is_authenticated is True
            assert user.is_active is True
            assert user.is_anonymous is False
            assert user.get_id() == str(user.id)

    def test_username_property(self, app):
        """Test that username is extracted from email."""
        with app.app_context():
            user = User(email="john.doe@example.com", password_hash="hash")
            assert user.username == "john.doe"

    def test_username_with_plus_sign(self, app):
        """Test username extraction with plus addressing."""
        with app.app_context():
            user = User(email="user+tag@example.com", password_hash="hash")
            assert user.username == "user+tag"

    def test_username_with_multiple_at_signs(self, app):
        """Test username extraction when email has multiple @ (edge case)."""
        with app.app_context():
            # This is technically invalid but tests the rsplit behavior
            user = User(email="user@company@example.com", password_hash="hash")
            assert user.username == "user@company"
