import pydash
from rotten_tomatoes_scraper.rt_scraper import MovieScraper


def fetch_movie_ratings_from_rt(movie_title: str):
    movie_scrapper = MovieScraper(movie_title=movie_title)
    try:
        movie_scrapper.extract_metadata()
        rating = pydash.get(movie_scrapper.metadata, "Score_Rotten", 0.0)
        return float(rating) / 10
    except:
        return 0.0
