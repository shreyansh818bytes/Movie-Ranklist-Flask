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


def _fetch_rt_page(movie_url: str) -> dict:
    """Fetch and parse a single RT page. Returns movie data dict."""
    movie_data = {"rating": 0.0, "page_url": "", "year": None}

    try:
        response = requests.get(movie_url, headers=RT_HEADERS, timeout=10)

        if response.status_code != 200:
            return movie_data

        movie_data["page_url"] = movie_url

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract rating and year from JSON-LD structured data
        script_tags = soup.find_all("script", type="application/ld+json")
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if "aggregateRating" in data:
                    rating_value = data["aggregateRating"].get("ratingValue")
                    if rating_value:
                        # RT scores are 0-100, convert to 0-10 scale
                        movie_data["rating"] = float(rating_value) / 10

                # Extract year from datePublished or dateCreated
                date_published = data.get("datePublished") or data.get("dateCreated")
                if date_published and len(date_published) >= 4:
                    movie_data["year"] = int(date_published[:4])

                if movie_data["rating"] > 0:
                    break
            except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                continue

    except requests.exceptions.RequestException:
        pass

    return movie_data


def fetch_movie_data_from_rt(movie_title: str, year: int = None):
    """
    Fetch Rotten Tomatoes rating by scraping the movie page.
    Tries year-suffixed URL first (e.g., joker_2019), then falls back to title-only.
    Returns: { rating: float (0-10 scale), page_url: str, year: int or None }
    """
    slug = _title_to_slug(movie_title)

    # Try year-suffixed URL first if year is provided (e.g., joker_2019)
    if year:
        movie_url_with_year = f"https://www.rottentomatoes.com/m/{slug}_{year}"
        result = _fetch_rt_page(movie_url_with_year)
        if result["rating"] > 0:
            return result

    # Fall back to title-only URL (e.g., joker)
    movie_url = f"https://www.rottentomatoes.com/m/{slug}"
    return _fetch_rt_page(movie_url)
