import pydash
import requests

from ..env_variables import EnvVariable
from .exception_handler import handle_api_exception


@handle_api_exception
def fetch_movie_data_from_tmdb(
    title: str,
    year: int,
):
    params = {
        "api_key": EnvVariable.TMDB_API_KEY.value,
        "language": "en-US",
        "query": title,
        "include_adult": True,
    }
    if year:
        params["year"] = year

    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params=params,
        timeout=5,
    ).json()

    return pydash.get(response, "results[0]", None)
