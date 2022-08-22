import os

import pydash
import requests


def fetch_movie_ratings_from_imdb(
    movie_title: str, movie_release_date: str, movie_year: int
):
    url = "https://imdb8.p.rapidapi.com/title/v2/find"

    querystring = {
        "title": movie_title,
        "limit": "1",
        "sortArg": "release_date,desc",
    }
    if len(movie_release_date):
        querystring["releaseDateMax"] = movie_release_date
        querystring["releaseDateMin"] = movie_release_date
    else:
        querystring["releaseDateMax"] = f"{str(movie_year)}-12-31"

    headers = {
        "X-RapidAPI-Key": os.environ.get("IMDB_API_KEY"),
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring).json()

    return pydash.get(response, "results[0].ratings.rating", 0)
