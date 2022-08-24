import re
from typing import List


class MovieList:
    class Movie:
        def __init__(self, search: str, title: str, year: int = 0) -> None:
            self.id = hash(("search", search))
            self.search_query = search
            self.title = title
            self.year = year
            self.logo_url = "static/assets/not-found-icon.svg"
            self.details_request = {
                "is_pending": False,
                "is_successful": False,
            }
            self.imdb_data = {
                "rating": 0.0,
                "poster_url": "",
                "title_type": "",
                "page_url": "/not-found",
            }
            self.tmdb_data = {
                "rating": 0.0,
                "backdrop_url": "",
                "page_url": "/not-found",
            }
            self.rt_data = {
                "rating": 0.0,
                "page_url": "/not-found",
            }
            self.average_score = 0.0

        def __eq__(self, other: object) -> bool:
            return self.id == other.id

        def __hash__(self) -> int:
            return hash(("id", self.id))

    def __init__(self, movie_names_list: List[str] = []):
        self.list: List[self.Movie] = []
        self.total = 0
        self.append_from_string_list(movie_names_list)

    def append_from_string_list(self, movie_names_list: List[str]):
        for movie_search in movie_names_list:
            if not len(movie_search):
                continue
            year = 0
            title = movie_search
            regex_to_find_year = r"1[89][0-9][0-9]|2[0-9][0-9][0-9]"
            match_year_list = re.search(regex_to_find_year, movie_search)
            if match_year_list:
                year = int(match_year_list[0])
                title = re.sub(regex_to_find_year, "", movie_search)
            movie = self.Movie(movie_search, title, year)
            self.list.append(movie)
            self.total += 1
