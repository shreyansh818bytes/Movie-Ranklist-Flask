from flask import Flask, redirect, render_template, request, session

from flask_session import Session
from utils.helpers import (
    fetch_movie_details_helper,
    movie_delete_handler,
    movie_search_handler,
)
from utils.objects import MovieList

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
Session(app)


@app.route("/ping", methods=["GET"])
def ping():
    return "pong"


@app.route("/search", methods=["POST"])
def search():
    if request.form:
        movie_list_in_search = movie_search_handler(request.form)
        session["movies_list"].append_from_string_list(movie_list_in_search)

    return redirect("/")


@app.route("/delete", methods=["POST"])
def delete():
    if request.form:
        movie_delete_handler(
            movie_id=request.form["movie_id"], movie_list=session["movies_list"]
        )

    return redirect("/")


@app.route("/", methods=["GET"])
def index():
    if not session.get("movies_list"):
        session["movies_list"] = MovieList()
    fetch_movie_details_helper(session["movies_list"])

    return render_template("index.html", movies_list=session["movies_list"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
