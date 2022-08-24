import os

import pydash
import requests

from .exception_handler import handle_api_exception

IMDB_API_KEY = os.environ.get("IMDB_API_KEY")


def pick_top_valid_result(results):
    for result in results:
        if (
            "titleType" in result
            and result["titleType"]
            in [
                "movie",
                "tvSeries",
                "tvEpisode",
                "tvMiniSeries",
                "tvMovie",
                "tvSpecial",
                "short",
                "tvShort",
            ]
            and "id" in result
            and "title" in result
            and str(result["id"]).find("title") != -1
        ):
            return result
    return None


@handle_api_exception
def get_top_search_result(q: str):
    url = "https://imdb8.p.rapidapi.com/title/find"
    querystring = {
        "q": q,
    }
    headers = {
        "X-RapidAPI-Key": IMDB_API_KEY,
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring).json()

    top_results = pydash.get(response, "results", None)

    return pick_top_valid_result(top_results)


@handle_api_exception
def fetch_movie_data_from_imdb(query: str):
    top_result = get_top_search_result(query)

    if top_result is None:
        return None
    # Extract metadata
    image_url = pydash.get(top_result, "image.url", "")
    title_type = pydash.get(top_result, "titleType", "")
    # Extract title id
    title_id = top_result["id"]
    title_const = str(title_id).replace("/", "").replace("title", "")

    # Get movie data
    url = "https://imdb8.p.rapidapi.com/title/get-ratings"
    query_params = {"tconst": title_const}
    headers = {
        "X-RapidAPI-Key": IMDB_API_KEY,
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers, params=query_params).json()
    response["image_url"] = image_url
    response["title_type"] = title_type
    return response
