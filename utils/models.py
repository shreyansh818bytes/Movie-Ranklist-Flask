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

    # Relationship to watchlist entries
    watchlist_entries = db.relationship(
        "WatchlistEntry", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

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


class Movie(db.Model):
    """
    Stores movie metadata and ratings.
    Movies are shared across users - the WatchlistEntry table links users to movies.
    """

    __tablename__ = "movies"

    id = db.Column(db.String(20), primary_key=True)  # IMDb ID (e.g., tt0133093)
    title = db.Column(db.String(500), nullable=False)
    year = db.Column(db.Integer)
    logo_url = db.Column(db.String(1000))  # Poster image
    backdrop_url = db.Column(db.String(1000))  # Backdrop image (standard)
    backdrop_url_hd = db.Column(db.String(1000))  # Backdrop image (HD)

    # Ratings
    imdb_rating = db.Column(db.Float)
    imdb_page_url = db.Column(db.String(500))
    tmdb_rating = db.Column(db.Float)
    tmdb_page_url = db.Column(db.String(500))
    rt_tomatometer = db.Column(db.Float)  # Critics score (0-10)
    rt_popcornmeter = db.Column(db.Float)  # Audience score (0-10)
    rt_page_url = db.Column(db.String(500))

    # Genre from IMDB
    genres = db.Column(db.JSON)  # e.g., ["Action", "Sci-Fi"]

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ratings_updated_at = db.Column(db.DateTime)

    # Relationship to watchlist entries
    watchlist_entries = db.relationship(
        "WatchlistEntry", backref="movie", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "logo_url": self.logo_url,
            "backdrop_url": self.backdrop_url,
            "backdrop_url_hd": self.backdrop_url_hd,
            "imdb_rating": self.imdb_rating,
            "imdb_page_url": self.imdb_page_url,
            "tmdb_rating": self.tmdb_rating,
            "tmdb_page_url": self.tmdb_page_url,
            "rt_tomatometer": self.rt_tomatometer,
            "rt_popcornmeter": self.rt_popcornmeter,
            "rt_page_url": self.rt_page_url,
            "genres": self.genres,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ratings_updated_at": (
                self.ratings_updated_at.isoformat() if self.ratings_updated_at else None
            ),
        }

    def calculate_average_score(self):
        """Calculate average score from all available platform ratings."""
        scores = []
        if self.imdb_rating and self.imdb_rating > 0:
            scores.append(self.imdb_rating)
        if self.tmdb_rating and self.tmdb_rating > 0:
            scores.append(self.tmdb_rating)
        # Use tomatometer as the primary RT score for average
        if self.rt_tomatometer and self.rt_tomatometer > 0:
            scores.append(self.rt_tomatometer)
        if not scores:
            return 0
        return round(sum(scores) / len(scores), 1)


class WatchlistEntry(db.Model):
    """
    Junction table linking users to movies in their watchlist.
    Each user can have each movie only once in their watchlist.
    """

    __tablename__ = "watchlist_entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.String(20), db.ForeignKey("movies.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "movie_id", name="uq_user_movie"),)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "movie": self.movie.to_dict() if self.movie else None,
        }
