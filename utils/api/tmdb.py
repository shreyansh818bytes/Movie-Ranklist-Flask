import os

import requests

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")


def fetch_movie_details_from_tmdb(
    name: str,
    year: int = 0,
):
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "query": name,
        "inclue_adult": True,
    }
    if year:
        params["year"] = year

    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params=params,
        timeout=5,
    )
    return response.json()
