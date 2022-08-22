import os
import requests
import pydash


def fetch_movie_ratings_from_imdb(movie_title):
    url = "https://imdb8.p.rapidapi.com/title/v2/find"

    querystring = {"title": movie_title, "limit": "1", "sortArg": "moviemeter,asc"}

    headers = {
        "X-RapidAPI-Key": os.environ.get("IMDB_API_KEY"),
        "X-RapidAPI-Host": "imdb8.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring).json()
    
    return pydash.get(response, 'results[0].ratings.rating', 0)
