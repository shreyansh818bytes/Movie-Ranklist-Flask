from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_migrate import Migrate
from waitress import serve

from utils.auth import authenticate_user, register_user
from utils.env_variables import EnvVariable
from utils.helpers import (
    fetch_imdb_rating,
    fetch_rt_rating,
    fetch_tmdb_rating,
    search_movies_parallel,
)
from utils.models import User, db
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
def index():
    return render_template("index.html")


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
