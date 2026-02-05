import pydash
import requests

from ..env_variables import EnvVariable
from .exception_handler import handle_api_exception


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
        "X-RapidAPI-Key": EnvVariable.IMDB_API_KEY.value,
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring).json()

    top_results = pydash.get(response, "results", None)

    if top_results is None:
        return None
    return pick_top_valid_result(top_results)


@handle_api_exception
def search_imdb(query: str):
    """
    Search IMDb for a movie and return metadata only (no rating).
    Returns: { id, title, year, image_url, page_url } or None
    """
    top_result = get_top_search_result(query)

    if top_result is None:
        return None

    # Extract title id (tconst format like tt0133093)
    title_id = top_result["id"]
    tconst = str(title_id).replace("/", "").replace("title", "")

    return {
        "id": tconst,
        "title": pydash.get(top_result, "title", ""),
        "year": pydash.get(top_result, "year", None),
        "image_url": pydash.get(top_result, "image.url", ""),
        "page_url": f"https://www.imdb.com{title_id}",
        "title_type": pydash.get(top_result, "titleType", ""),
    }


@handle_api_exception
def get_imdb_rating(tconst: str):
    """
    Get IMDb rating for a movie by tconst (e.g., tt0133093).
    Returns: { rating, page_url } or None
    """
    url = "https://imdb8.p.rapidapi.com/title/get-ratings"
    query_params = {"tconst": tconst}
    headers = {
        "X-RapidAPI-Key": EnvVariable.IMDB_API_KEY.value,
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers, params=query_params).json()

    rating = pydash.get(response, "rating", None)
    if rating is not None:
        rating = round(float(rating), 1)

    return {
        "rating": rating,
        "page_url": f"https://www.imdb.com/title/{tconst}/",
    }


@handle_api_exception
def get_imdb_genres(tconst: str):
    """
    Get genres for a movie by tconst (e.g., tt0133093).
    Returns: { genres: ["Action", "Sci-Fi", ...] } or None
    """
    url = "https://imdb8.p.rapidapi.com/title/get-genres"
    query_params = {"tconst": tconst}
    headers = {
        "X-RapidAPI-Key": EnvVariable.IMDB_API_KEY.value,
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers, params=query_params).json()

    # Response is typically a list of genre strings
    if isinstance(response, list):
        return {"genres": response}

    # Some responses might have genres nested
    genres = pydash.get(response, "genres", [])
    return {"genres": genres if isinstance(genres, list) else []}
