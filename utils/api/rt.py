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
    """
    Fetch and parse a single RT page.
    Returns movie data dict with both tomatometer (critics) and popcornmeter (audience) scores.
    """
    movie_data = {
        "tomatometer": 0.0,  # Critics score
        "popcornmeter": 0.0,  # Audience score
        "rating": 0.0,  # Legacy: same as tomatometer for backwards compatibility
        "page_url": "",
        "year": None,
    }

    try:
        response = requests.get(movie_url, headers=RT_HEADERS, timeout=10)

        if response.status_code != 200:
            return movie_data

        movie_data["page_url"] = movie_url

        soup = BeautifulSoup(response.text, "html.parser")

        # Try to extract scores from score-board or media-scorecard elements
        # RT uses custom elements for displaying scores
        score_board = soup.find("score-board") or soup.find("media-scorecard")

        if score_board:
            # Extract tomatometer (critics score)
            tomatometer = score_board.get("tomatometerscore") or score_board.get(
                "criticsscore"
            )
            if tomatometer:
                try:
                    movie_data["tomatometer"] = float(tomatometer) / 10
                    movie_data["rating"] = movie_data["tomatometer"]
                except (ValueError, TypeError):
                    pass

            # Extract popcornmeter (audience score)
            popcornmeter = score_board.get("audiencescore")
            if popcornmeter:
                try:
                    movie_data["popcornmeter"] = float(popcornmeter) / 10
                except (ValueError, TypeError):
                    pass

        # Fallback: Extract from JSON-LD structured data
        if movie_data["tomatometer"] == 0:
            script_tags = soup.find_all("script", type="application/ld+json")
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if "aggregateRating" in data:
                        rating_value = data["aggregateRating"].get("ratingValue")
                        if rating_value:
                            # RT scores are 0-100, convert to 0-10 scale
                            movie_data["tomatometer"] = float(rating_value) / 10
                            movie_data["rating"] = movie_data["tomatometer"]

                    # Extract year from datePublished or dateCreated
                    date_published = data.get("datePublished") or data.get(
                        "dateCreated"
                    )
                    if date_published and len(date_published) >= 4:
                        movie_data["year"] = int(date_published[:4])

                    if movie_data["tomatometer"] > 0:
                        break
                except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                    continue

        # Try to extract audience score from dedicated elements if not found
        if movie_data["popcornmeter"] == 0:
            # Look for audience score in various possible locations
            audience_elements = soup.find_all(
                attrs={"data-qa": "audience-score"}
            ) or soup.find_all(class_=re.compile(r"audience.*score", re.I))
            for elem in audience_elements:
                score_text = elem.get_text(strip=True)
                # Extract number from text like "91%" or "91"
                match = re.search(r"(\d+)", score_text)
                if match:
                    try:
                        movie_data["popcornmeter"] = float(match.group(1)) / 10
                        break
                    except (ValueError, TypeError):
                        continue

    except requests.exceptions.RequestException:
        pass

    return movie_data


def fetch_movie_data_from_rt(movie_title: str, year: int = None):
    """
    Fetch Rotten Tomatoes ratings by scraping the movie page.
    Tries year-suffixed URL first (e.g., joker_2019), then falls back to title-only.
    Returns: {
        tomatometer: float (0-10 scale, critics score),
        popcornmeter: float (0-10 scale, audience score),
        rating: float (same as tomatometer for backwards compatibility),
        page_url: str,
        year: int or None
    }
    """
    slug = _title_to_slug(movie_title)

    # Try year-suffixed URL first if year is provided (e.g., joker_2019)
    if year:
        movie_url_with_year = f"https://www.rottentomatoes.com/m/{slug}_{year}"
        result = _fetch_rt_page(movie_url_with_year)
        if result["tomatometer"] > 0 or result["popcornmeter"] > 0:
            return result

    # Fall back to title-only URL (e.g., joker)
    movie_url = f"https://www.rottentomatoes.com/m/{slug}"
    return _fetch_rt_page(movie_url)
