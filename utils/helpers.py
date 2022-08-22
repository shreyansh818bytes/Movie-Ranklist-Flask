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


def map_json_to_movie_details(json_response, movie):
    movie_details = {
        "id": hash(("title", movie.title)),
        "logo_url": "",
        "title": movie.title,
        "year": movie.year,
        "tmdb_score": 0,
    }
    request_successful = False

    if "results" in json_response and len(json_response["results"]):
        first_result = json_response["results"][0]
        if "release_date" in first_result:
            year = first_result["release_date"].split("-")[0]
            first_result["year"] = year
        movie_details["id"] = first_result["id"]
        movie_details["title"] = first_result["title"]
        movie_details["year"] = first_result["year"] if "year" in first_result else 0
        tmdb_image_url = "https://image.tmdb.org/t/p/original"
        movie_details["tmdb_score"] = first_result["vote_average"]
        if first_result["backdrop_path"] is not None:
            movie_details["logo_url"] = tmdb_image_url + first_result["backdrop_path"]
        else:
            movie_details["logo_url"] = "static/assets/not-found-icon.svg"
        request_successful = True
    else:
        movie_details["logo_url"] = "static/assets/not-found-icon.svg"

    return (request_successful, movie_details)


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
                    movie_title=movie.fetched_details["title"]
                )
                movie.fetched_details["rt_score"] = fetch_movie_ratings_from_rt(
                    movie_title=movie.fetched_details["title"]
                )
                movie.fetched_details["average_score"] = get_average_movie_score(movie)

    movie_list.list = list(set(movie_list.list))  # Removing duplicates
    movie_list.list.sort(
        key=lambda movie: movie.fetched_details["average_score"], reverse=True
    )
