import re
from typing import List


class MovieList:
    class Movie:
        def __init__(self, title: str, year: int = 0) -> None:
            self.title = title
            self.year = year
            self.details_request = {
                "is_pending": False,
                "is_successful": False,
            }
            self.fetched_details = {
                "id": "",
                "title": "",
                "year": 0,
                "logo_url": "",
                "tmdb_score": 0.0,
                "imdb_score": 0.0,
                "rt_score": 0.0,
                "average_score": 0.0,
            }

        def __eq__(self, other: object) -> bool:
            is_both_successfully_fetched = (
                self.details_request["is_successful"]
                and other.details_request["is_successful"]
            )
            return (
                is_both_successfully_fetched
                and self.fetched_details["id"] == other.fetched_details["id"]
            )

        def __hash__(self) -> int:
            if self.details_request["is_successful"]:
                return hash(("tmdb_id", self.fetched_details["id"]))
            return hash(("title", self.title, "year", self.year))

    def __init__(self, movie_names_list: List[str] = []):
        self.list: List[self.Movie] = []
        self.total = 0
        self.append_from_string_list(movie_names_list)

    def append_from_string_list(self, movie_names_list: List[str]):
        for movie_name in movie_names_list:
            if not len(movie_name):
                continue
            year = 0
            regex_to_find_year = r"1[89][0-9][0-9]|2[0-9][0-9][0-9]"
            match_year_list = re.search(regex_to_find_year, movie_name)
            if match_year_list:
                year = int(match_year_list[0])
                movie_name = re.sub(regex_to_find_year, "", movie_name)
            movie = self.Movie(movie_name, year)
            self.list.append(movie)
            self.total += 1
