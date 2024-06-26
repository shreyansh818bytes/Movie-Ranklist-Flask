# App wide helper and handler functions
from .api.imdb import fetch_movie_data_from_imdb
from .api.tmdb import fetch_movie_data_from_tmdb
from .objects import MovieList


# Handlers.
def movie_search_handler(data):
    movie_list = []
    if data["searchStringList"]:
        movie_list.extend(
            [
                movie_string.replace("\r", "")
                for movie_string in data["searchStringList"]
                if len(movie_string)
            ]
        )
    return movie_list


def movie_delete_handler(movie_id, movie_list: MovieList):
    movie: MovieList.Movie
    for movie in movie_list.list:
        if str(movie.id) == str(movie_id):
            movie_list.list.remove(movie)


# Helpers.
def get_average_movie_score(movie: MovieList.Movie) -> float:
    score_list = [
        float(movie.imdb_data["rating"]),
        float(movie.tmdb_data["rating"]),
        float(movie.rt_data["rating"]),
    ]
    filtered_scores = [x for x in score_list if x]

    if not len(filtered_scores):
        return 0

    return float(sum(filtered_scores) / len(filtered_scores))


# Mappers.
def map_imdb_data_to_movie_object(movie_data, movie: MovieList.Movie) -> None:
    movie.id = movie_data["id"]
    movie.title = movie_data["title"]
    movie.year = int(movie_data["year"])
    if len(movie_data["image_url"]):
        movie.logo_url = movie_data["image_url"]
        movie.imdb_data["poster_url"] = movie_data["image_url"]
    if "rating" in movie_data:
        movie.imdb_data["rating"] = round(float(movie_data["rating"]), 1)
    movie.imdb_data["title_type"] = movie_data["title_type"]
    movie.imdb_data["page_url"] = movie_data["page_url"]


def map_tmdb_data_to_movie_object(movie_data, movie: MovieList.Movie) -> None:
    movie.tmdb_data["rating"] = round(float(movie_data["vote_average"]), 1)
    movie.tmdb_data["page_url"] = "https://www.themoviedb.org/movie/" + str(
        movie_data["id"]
    )
    if movie_data["backdrop_path"] is not None:
        tmdb_image_url = (
            "https://image.tmdb.org/t/p/original" + movie_data["backdrop_path"]
        )
        movie.tmdb_data["backdrop_url"] = tmdb_image_url
        movie.logo_url = tmdb_image_url


def map_rt_data_to_movie_object(movie_data, movie: MovieList.Movie) -> None:
    movie.rt_data["rating"] = round(float(movie_data["rating"]), 1)
    if len(movie_data["page_url"]):
        movie.rt_data["page_url"] = movie_data["page_url"]


# API Helper.
def fetch_movie_details_helper(movie_list: MovieList):
    movie: MovieList.Movie
    for movie in movie_list.list:
        if not movie.details_request["is_successful"]:
            # Fetch data from IMDb
            imdb_api_response = fetch_movie_data_from_imdb(movie.search_query)
            if imdb_api_response is not None:
                map_imdb_data_to_movie_object(
                    imdb_api_response,
                    movie,
                )

            # Fetch data from TMDb
            tmdb_api_response = fetch_movie_data_from_tmdb(
                title=movie.title, year=movie.year
            )
            if tmdb_api_response is not None:
                map_tmdb_data_to_movie_object(
                    tmdb_api_response,
                    movie,
                )

            # Fetch data from Rotten Tomatoes
            # Scrapper is not supported anymore. Disabling Rotten Tomatoes ratings for now.
            # map_rt_data_to_movie_object(
            #     fetch_movie_data_from_rt(
            #         movie_title=movie.title,
            #     ),
            #     movie,
            # )

            movie.details_request["is_successful"] = True

            movie.average_score = get_average_movie_score(movie)

    movie_list.list = list(set(movie_list.list))  # Removing duplicates
    movie_list.list.sort(key=lambda movie: movie.average_score, reverse=True)
