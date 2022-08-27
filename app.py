from flask import Flask, render_template, request, session

from flask_session import Session
from utils.helpers import (
    fetch_movie_details_helper,
    movie_delete_handler,
    movie_search_handler,
)
from utils.objects import MovieList, Response

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
Session(app)


@app.route("/ping", methods=["GET"])
def ping():
    return "pong"


@app.route("/search", methods=["POST"])
def search():
    if request.json:
        movie_list_in_search = movie_search_handler(request.json)
        session["movies_list"].append_from_string_list(movie_list_in_search)
        # Use threading for this route
        fetch_movie_details_helper(session["movies_list"])
        # explore turbo to update html on above function completes execution

        return Response(
            response={
                "message": "Movies added successfully!",
                "data": {"total": len(session["movies_list"].list)},
            }
        )

    return Response(
        response={"message": "Request body not found."},
        status=400,
    )


@app.route("/delete", methods=["POST"])
def delete():
    if request.json:
        movie_delete_handler(
            movie_id=request.json["movieId"], movie_list=session["movies_list"]
        )

        return Response(
            response={
                "message": "Movie deleted successfully!",
                "data": {"total": len(session["movies_list"].list)},
            }
        )

    return Response(response={"message": "Response body not found."}, status=400)


@app.route("/", methods=["GET"])
def index():
    if not session.get("movies_list"):
        session["movies_list"] = MovieList()

    return render_template("index.html", movies_list=session["movies_list"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
