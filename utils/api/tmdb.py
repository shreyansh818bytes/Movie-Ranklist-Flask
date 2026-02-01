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

    result = pydash.get(response, "results[0]", None)
    if result:
        # Extract year from release_date (format: "YYYY-MM-DD")
        release_date = result.get("release_date", "")
        if release_date and len(release_date) >= 4:
            result["year"] = int(release_date[:4])
        else:
            result["year"] = None
    return result
