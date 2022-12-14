import os

import pydash
import requests

from .exception_handler import handle_api_exception

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")


@handle_api_exception
def fetch_movie_data_from_tmdb(
    title: str,
    year: int,
):
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "query": title,
        "inclue_adult": True,
    }
    if year:
        params["year"] = year

    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params=params,
        timeout=5,
    ).json()

    return pydash.get(response, "results[0]", None)
