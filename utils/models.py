from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # NULL for OAuth users
    auth_provider = db.Column(db.String(50), default="local")  # 'local', 'google'
    oauth_id = db.Column(db.String(255), nullable=True)  # For future OAuth
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def username(self):
        """Extract username from email (everything before the last '@')."""
        if self.email and "@" in self.email:
            return self.email.rsplit("@", 1)[0]
        return self.email

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "auth_provider": self.auth_provider,
        }
