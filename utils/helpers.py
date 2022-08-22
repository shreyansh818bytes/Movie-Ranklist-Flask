# App wide helper and handler functions
from .api.imdb import fetch_movie_ratings_from_imdb
from .api.rt import fetch_movie_ratings_from_rt
from .api.tmdb import fetch_movie_details_from_tmdb
from .objects import MovieList


# Handlers.
def movie_search_handler(request_form):
    movie_list = []
    if request_form["single_text"]:
        movie_list.append(request_form["single_text"])
    if request_form["multiple_text"]:
        movie_names_string = request_form["multiple_text"]
        movie_list.extend(
            [movie.replace("\r", "") for movie in movie_names_string.split("\n")]
        )
    return movie_list


def movie_delete_handler(movie_id, movie_list: MovieList):
    for movie in movie_list.list:
        if str(movie.fetched_details["id"]) == str(movie_id):
            movie_list.list.remove(movie)


# Helpers.
def get_average_movie_score(movie: MovieList.Movie) -> float:
    score_list = [
        float(movie.fetched_details["imdb_score"]),
        float(movie.fetched_details["tmdb_score"]),
        float(movie.fetched_details["rt_score"]),
    ]
    filtered_scores = [x for x in score_list if x]

    return float(sum(filtered_scores) / len(filtered_scores))


def map_json_to_movie_details(movie_data, movie):
    movie_details = {
        "id": hash(("title", movie.title)),
        "logo_url": "static/assets/not-found-icon.svg",
        "title": movie.title,
        "year": movie.year,
        "tmdb_score": 0,
        "release_date": "",
    }

    if not movie_data:
        return (False, movie_details)

    if "release_date" in movie_data:
        movie_details["year"] = movie_data["release_date"].split("-")[0]
        movie_details["release_date"] = movie_data["release_date"]
    movie_details["id"] = movie_data["id"]
    movie_details["title"] = movie_data["title"]
    movie_details["tmdb_score"] = movie_data["vote_average"]
    tmdb_image_url = "https://image.tmdb.org/t/p/original"
    if movie_data["backdrop_path"] is not None:
        movie_details["logo_url"] = tmdb_image_url + movie_data["backdrop_path"]

    return (True, movie_details)


def fetch_movie_details_helper(movie_list: MovieList):
    movie: MovieList.Movie
    for movie in movie_list.list:
        if not movie.details_request["is_successful"]:
            movie.details_request["is_pending"] = True
            (is_request_successful, tmdb_fetched_details) = map_json_to_movie_details(
                fetch_movie_details_from_tmdb(movie.title, movie.year),
                movie,
            )

            for key, value in tmdb_fetched_details.items():
                movie.fetched_details[key] = value

            movie.details_request = {
                "is_pending": False,
                "is_successful": is_request_successful,
            }

            if is_request_successful:
                movie.fetched_details["imdb_score"] = fetch_movie_ratings_from_imdb(
                    movie_title=movie.fetched_details["title"],
                    movie_release_date=movie.fetched_details["release_date"],
                    movie_year=int(movie.fetched_details["year"]),
                )
                movie.fetched_details["rt_score"] = fetch_movie_ratings_from_rt(
                    movie_title=movie.fetched_details["title"]
                )
                movie.fetched_details["average_score"] = get_average_movie_score(movie)

    movie_list.list = list(set(movie_list.list))  # Removing duplicates
    movie_list.list.sort(
        key=lambda movie: movie.fetched_details["average_score"], reverse=True
    )
