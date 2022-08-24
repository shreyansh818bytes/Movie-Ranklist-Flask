import pydash
from rotten_tomatoes_scraper.rt_scraper import MovieScraper


def fetch_movie_data_from_rt(movie_title: str):
    movie_data = {"rating": 0.0, "page_url": ""}
    try:
        movie_scrapper = MovieScraper(movie_title=movie_title)
        movie_scrapper.extract_metadata()
        movie_data["rating"] = (
            int(pydash.get(movie_scrapper.metadata, "Score_Rotten", 0)) / 10
        )
        movie_data["page_url"] = movie_scrapper.url
    finally:
        return movie_data
