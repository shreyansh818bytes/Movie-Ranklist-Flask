import json
import re

import requests
from bs4 import BeautifulSoup

RT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _title_to_slug(title: str) -> str:
    """Convert movie title to RT URL slug format."""
    # Remove special characters and convert to lowercase with underscores
    slug = title.lower()
    # Remove common punctuation
    slug = re.sub(r"[':!?,.\-\(\)]", "", slug)
    # Replace spaces with underscores
    slug = re.sub(r"\s+", "_", slug)
    return slug


def fetch_movie_data_from_rt(movie_title: str):
    """
    Fetch Rotten Tomatoes rating by scraping the movie page.
    Returns: { rating: float (0-10 scale), page_url: str }
    """
    movie_data = {"rating": 0.0, "page_url": ""}

    try:
        slug = _title_to_slug(movie_title)
        movie_url = f"https://www.rottentomatoes.com/m/{slug}"

        response = requests.get(movie_url, headers=RT_HEADERS, timeout=10)

        if response.status_code != 200:
            return movie_data

        movie_data["page_url"] = movie_url

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract rating from JSON-LD structured data
        script_tags = soup.find_all("script", type="application/ld+json")
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if "aggregateRating" in data:
                    rating_value = data["aggregateRating"].get("ratingValue")
                    if rating_value:
                        # RT scores are 0-100, convert to 0-10 scale
                        movie_data["rating"] = float(rating_value) / 10
                        break
            except (json.JSONDecodeError, TypeError, KeyError):
                continue

    except requests.exceptions.RequestException:
        pass

    return movie_data
