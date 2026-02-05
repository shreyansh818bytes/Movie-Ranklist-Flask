from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_migrate import Migrate
from waitress import serve

from utils.auth import authenticate_user, register_user
from utils.env_variables import EnvVariable
from utils.helpers import (
    fetch_imdb_genres,
    fetch_imdb_rating,
    fetch_rt_rating,
    fetch_tmdb_rating,
    search_movies_parallel,
)
from utils.models import Movie, User, WatchlistEntry, db
from utils.objects import Response

app = Flask(__name__)
app.config["SECRET_KEY"] = EnvVariable.SECRET_KEY.value
app.config["SQLALCHEMY_DATABASE_URI"] = EnvVariable.DATABASE_URL.value
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    """Return JSON 401 for API requests, redirect for page requests."""
    if request.path.startswith("/api/"):
        return (
            jsonify({"error": "Authentication required", "authenticated": False}),
            401,
        )
    return redirect(url_for("login"))


with app.app_context():
    db.create_all()


@app.route("/ping", methods=["GET"])
def ping():
    return "pong"


@app.route("/api/movies/search", methods=["POST"])
def search_movies():
    """
    Search for movies and return metadata only (no ratings).
    Accepts: {"movies": [{"query": "The Matrix 1999"}, ...]}
    Returns: {"movies": [{"id": "tt0133093", "query": "...", "title": "...", "year": 1999, "logo_url": "..."}], "errors": [...]}
    """
    if not request.json or "movies" not in request.json:
        return Response(
            response={"error": "Request must include 'movies' array"},
            status=400,
        )

    queries = request.json["movies"]
    if not isinstance(queries, list):
        return Response(
            response={"error": "'movies' must be an array"},
            status=400,
        )

    result = search_movies_parallel(queries)
    return Response(response={"movies": result["movies"], "errors": result["errors"]})


@app.route("/api/movies/<movie_id>/rating/<platform>", methods=["GET"])
def get_movie_rating(movie_id, platform):
    """
    Get rating for a specific movie from a specific platform.
    Platforms: imdb, tmdb, rt
    Query params for tmdb: title, year
    Query params for rt: title, year
    Returns: {"rating": 8.7, "page_url": "...", ...}
    """
    platform = platform.lower()

    if platform == "imdb":
        result = fetch_imdb_rating(movie_id)
        return Response(response=result)

    elif platform == "tmdb":
        title = request.args.get("title", "")
        year = request.args.get("year", type=int)
        if not title:
            return Response(
                response={"error": "Title is required for TMDb rating lookup"},
                status=400,
            )
        result = fetch_tmdb_rating(title, year)
        return Response(response=result)

    elif platform == "rt":
        title = request.args.get("title", "")
        year = request.args.get("year", type=int)
        if not title:
            return Response(
                response={"error": "Title is required for RT rating lookup"},
                status=400,
            )
        result = fetch_rt_rating(title, year)
        return Response(response=result)

    else:
        return Response(
            response={
                "error": f"Unknown platform: {platform}. Supported: imdb, tmdb, rt"
            },
            status=400,
        )


@app.route("/", methods=["GET"])
@app.route("/ranklist", methods=["GET"])
def index():
    return render_template("index.html")


# ==================== Watchlist API Routes ====================


@app.route("/api/watchlist", methods=["GET"])
@login_required
def get_watchlist():
    """
    Get user's watchlist with optional filters, sorting, and pagination.
    Query params:
    - genre: Filter by genre (e.g., "Action")
    - year_start, year_end: Filter by year range
    - min_rating: Minimum IMDB rating
    - search: Search in title
    - sort_by: "imdb", "rt_tomatometer", "rt_popcornmeter", "added_at", "year", "title"
    - sort_order: "asc" or "desc" (default: "desc")
    - page, per_page: Pagination (default: page=1, per_page=50)
    """
    # Get query parameters
    genre = request.args.get("genre")
    year_start = request.args.get("year_start", type=int)
    year_end = request.args.get("year_end", type=int)
    min_rating = request.args.get("min_rating", type=float)
    search = request.args.get("search")
    sort_by = request.args.get("sort_by", "added_at")
    sort_order = request.args.get("sort_order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # Base query: join WatchlistEntry with Movie for current user
    query = (
        db.session.query(WatchlistEntry, Movie)
        .join(Movie, WatchlistEntry.movie_id == Movie.id)
        .filter(WatchlistEntry.user_id == current_user.id)
    )

    # Apply filters
    if genre:
        # JSON contains check for genres array
        query = query.filter(Movie.genres.contains([genre]))

    if year_start:
        query = query.filter(Movie.year >= year_start)

    if year_end:
        query = query.filter(Movie.year <= year_end)

    if min_rating:
        query = query.filter(Movie.imdb_rating >= min_rating)

    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))

    # Apply sorting
    sort_column_map = {
        "imdb": Movie.imdb_rating,
        "rt_tomatometer": Movie.rt_tomatometer,
        "rt_popcornmeter": Movie.rt_popcornmeter,
        "added_at": WatchlistEntry.added_at,
        "year": Movie.year,
        "title": Movie.title,
    }

    sort_column = sort_column_map.get(sort_by, WatchlistEntry.added_at)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc().nullslast())
    else:
        query = query.order_by(sort_column.desc().nullsfirst())

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    per_page = min(per_page, 100)  # Cap at 100
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()

    # Build response
    movies = []
    for entry, movie in results:
        movie_dict = movie.to_dict()
        movie_dict["added_at"] = entry.added_at.isoformat() if entry.added_at else None
        movie_dict["average_score"] = movie.calculate_average_score()
        movies.append(movie_dict)

    return jsonify(
        {
            "movies": movies,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }
    )


@app.route("/api/watchlist", methods=["POST"])
@login_required
def add_to_watchlist():
    """
    Add a movie to the user's watchlist.
    Request body: {
        "movie_id": "tt0133093",
        "title": "The Matrix",
        "year": 1999,
        "logo_url": "...",
        "backdrop_url": "...",
        "backdrop_url_hd": "...",
        "imdb_rating": 8.7,
        "imdb_page_url": "...",
        "tmdb_rating": 8.2,
        "tmdb_page_url": "...",
        "rt_tomatometer": 8.8,
        "rt_popcornmeter": 8.5,
        "rt_page_url": "...",
        "genres": ["Action", "Sci-Fi"]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    movie_id = data.get("movie_id")
    if not movie_id:
        return jsonify({"success": False, "error": "movie_id is required"}), 400

    # Check if already in watchlist
    existing = WatchlistEntry.query.filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if existing:
        return jsonify({"success": False, "error": "Movie already in watchlist"}), 409

    # Get or create the movie
    movie = Movie.query.get(movie_id)
    if not movie:
        # Create new movie record
        title = data.get("title")
        if not title:
            return jsonify({"success": False, "error": "title is required"}), 400

        movie = Movie(
            id=movie_id,
            title=title,
            year=data.get("year"),
            logo_url=data.get("logo_url"),
            backdrop_url=data.get("backdrop_url"),
            backdrop_url_hd=data.get("backdrop_url_hd"),
            imdb_rating=data.get("imdb_rating"),
            imdb_page_url=data.get("imdb_page_url"),
            tmdb_rating=data.get("tmdb_rating"),
            tmdb_page_url=data.get("tmdb_page_url"),
            rt_tomatometer=data.get("rt_tomatometer"),
            rt_popcornmeter=data.get("rt_popcornmeter"),
            rt_page_url=data.get("rt_page_url"),
            genres=data.get("genres"),
            ratings_updated_at=datetime.utcnow(),
        )
        db.session.add(movie)
    else:
        # Update existing movie with any new data
        if data.get("imdb_rating") is not None:
            movie.imdb_rating = data.get("imdb_rating")
        if data.get("imdb_page_url"):
            movie.imdb_page_url = data.get("imdb_page_url")
        if data.get("tmdb_rating") is not None:
            movie.tmdb_rating = data.get("tmdb_rating")
        if data.get("tmdb_page_url"):
            movie.tmdb_page_url = data.get("tmdb_page_url")
        if data.get("rt_tomatometer") is not None:
            movie.rt_tomatometer = data.get("rt_tomatometer")
        if data.get("rt_popcornmeter") is not None:
            movie.rt_popcornmeter = data.get("rt_popcornmeter")
        if data.get("rt_page_url"):
            movie.rt_page_url = data.get("rt_page_url")
        if data.get("backdrop_url"):
            movie.backdrop_url = data.get("backdrop_url")
        if data.get("backdrop_url_hd"):
            movie.backdrop_url_hd = data.get("backdrop_url_hd")
        if data.get("genres"):
            movie.genres = data.get("genres")
        movie.ratings_updated_at = datetime.utcnow()

    # Create watchlist entry
    entry = WatchlistEntry(user_id=current_user.id, movie_id=movie_id)
    db.session.add(entry)
    db.session.commit()

    movie_dict = movie.to_dict()
    movie_dict["added_at"] = entry.added_at.isoformat()
    movie_dict["average_score"] = movie.calculate_average_score()

    return jsonify({"success": True, "movie": movie_dict})


@app.route("/api/watchlist/<movie_id>", methods=["DELETE"])
@login_required
def remove_from_watchlist(movie_id):
    """Remove a movie from the user's watchlist."""
    entry = WatchlistEntry.query.filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()

    if not entry:
        return jsonify({"success": False, "error": "Movie not in watchlist"}), 404

    db.session.delete(entry)
    db.session.commit()

    return jsonify({"success": True})


@app.route("/api/watchlist/bulk", methods=["POST"])
@login_required
def add_bulk_to_watchlist():
    """
    Add multiple movies to the user's watchlist.
    Request body: { "movies": [{ movie data }, ...] }
    """
    data = request.get_json()
    if not data or "movies" not in data:
        return jsonify({"success": False, "error": "movies array is required"}), 400

    movies_data = data["movies"]
    if not isinstance(movies_data, list):
        return jsonify({"success": False, "error": "movies must be an array"}), 400

    added = []
    skipped = []
    errors = []

    for movie_data in movies_data:
        movie_id = movie_data.get("movie_id")
        if not movie_id:
            errors.append({"movie_id": None, "error": "movie_id is required"})
            continue

        # Check if already in watchlist
        existing = WatchlistEntry.query.filter_by(
            user_id=current_user.id, movie_id=movie_id
        ).first()
        if existing:
            skipped.append(movie_id)
            continue

        # Get or create the movie
        movie = Movie.query.get(movie_id)
        if not movie:
            title = movie_data.get("title")
            if not title:
                errors.append({"movie_id": movie_id, "error": "title is required"})
                continue

            movie = Movie(
                id=movie_id,
                title=title,
                year=movie_data.get("year"),
                logo_url=movie_data.get("logo_url"),
                backdrop_url=movie_data.get("backdrop_url"),
                backdrop_url_hd=movie_data.get("backdrop_url_hd"),
                imdb_rating=movie_data.get("imdb_rating"),
                imdb_page_url=movie_data.get("imdb_page_url"),
                tmdb_rating=movie_data.get("tmdb_rating"),
                tmdb_page_url=movie_data.get("tmdb_page_url"),
                rt_tomatometer=movie_data.get("rt_tomatometer"),
                rt_popcornmeter=movie_data.get("rt_popcornmeter"),
                rt_page_url=movie_data.get("rt_page_url"),
                genres=movie_data.get("genres"),
                ratings_updated_at=datetime.utcnow(),
            )
            db.session.add(movie)

        # Create watchlist entry
        entry = WatchlistEntry(user_id=current_user.id, movie_id=movie_id)
        db.session.add(entry)
        added.append(movie_id)

    db.session.commit()

    return jsonify(
        {
            "success": True,
            "added": added,
            "added_count": len(added),
            "skipped": skipped,
            "skipped_count": len(skipped),
            "errors": errors,
        }
    )


@app.route("/api/watchlist/genres", methods=["GET"])
@login_required
def get_watchlist_genres():
    """Get all unique genres from user's watchlist for filter dropdown."""
    # Query all movies in user's watchlist
    movies = (
        db.session.query(Movie.genres)
        .join(WatchlistEntry, WatchlistEntry.movie_id == Movie.id)
        .filter(WatchlistEntry.user_id == current_user.id)
        .filter(Movie.genres.isnot(None))
        .all()
    )

    # Collect all unique genres
    all_genres = set()
    for (genres,) in movies:
        if genres and isinstance(genres, list):
            all_genres.update(genres)

    return jsonify({"genres": sorted(all_genres)})


@app.route("/api/movies/<movie_id>/genres", methods=["GET"])
def get_movie_genres(movie_id):
    """
    Get genres for a specific movie from IMDB.
    Returns: { genres: ["Action", "Sci-Fi", ...] }
    """
    result = fetch_imdb_genres(movie_id)
    return Response(response=result)


# Auth page routes
@app.route("/login", methods=["GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("auth/login.html")


@app.route("/register", methods=["GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("auth/register.html")


# Auth API routes
@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    email = data.get("email")
    password = data.get("password")

    user, error = register_user(email, password)
    if error:
        return jsonify({"success": False, "error": error}), 400

    return jsonify({"success": True, "user": user.to_dict()})


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    email = data.get("email")
    password = data.get("password")

    user, error = authenticate_user(email, password)
    if error:
        return jsonify({"success": False, "error": error}), 401

    login_user(user)
    return jsonify({"success": True, "user": user.to_dict()})


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/api/auth/status", methods=["GET"])
def api_auth_status():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "user": current_user.to_dict()})
    return jsonify({"authenticated": False})


if __name__ == "__main__":
    if EnvVariable.FLASK_DEBUG.value:
        app.run(
            host="0.0.0.0",
            port=int(EnvVariable.PORT.value),
            debug=True,
            use_reloader=True,
            reloader_type="stat",
        )
    else:
        serve(app, host="0.0.0.0", port=int(EnvVariable.PORT.value))
