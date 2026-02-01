# App wide helper and handler functions
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .api.imdb import get_imdb_rating, search_imdb
from .api.rt import fetch_movie_data_from_rt
from .api.tmdb import fetch_movie_data_from_tmdb

# In-memory cache with TTL (1 hour = 3600 seconds)
_cache = {}
_cache_ttl = 3600


def _get_cached(key):
    """Get value from cache if not expired."""
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < _cache_ttl:
            return value
        del _cache[key]
    return None


def _set_cached(key, value):
    """Set value in cache with current timestamp."""
    _cache[key] = (value, time.time())


def search_movie(query: str) -> dict:
    """
    Search for a movie and return metadata only (no ratings).
    Returns: { id, query, title, year, logo_url } or None
    """
    cache_key = f"search:{query}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    result = search_imdb(query)
    if result is None:
        return None

    movie_data = {
        "id": result["id"],
        "query": query,
        "title": result.get("title", ""),
        "year": result.get("year"),
        "logo_url": result.get("image_url", "static/assets/not-found-icon.svg"),
        "page_url": result.get("page_url", ""),
    }

    _set_cached(cache_key, movie_data)
    return movie_data


def fetch_imdb_rating(movie_id: str) -> dict:
    """
    Fetch IMDb rating by movie ID (tconst).
    Returns: { rating, page_url } or { rating: None, ... }
    """
    cache_key = f"imdb_rating:{movie_id}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    result = get_imdb_rating(movie_id)
    if result is None:
        result = {"rating": None, "page_url": f"https://www.imdb.com/title/{movie_id}/"}

    _set_cached(cache_key, result)
    return result


def _is_year_match(expected_year: int, actual_year: int, tolerance: int = 1) -> bool:
    """Check if years match within tolerance (default ±1 year for regional differences)."""
    if not expected_year or not actual_year:
        return True  # Skip validation if year is missing
    return abs(expected_year - actual_year) <= tolerance


def fetch_tmdb_rating(title: str, year: int = None) -> dict:
    """
    Fetch TMDb rating by title and year.
    Returns: { rating, page_url, backdrop_url, backdrop_url_hd } or { rating: None, ... }
    """
    cache_key = f"tmdb_rating:{title}:{year}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    result = fetch_movie_data_from_tmdb(title=title, year=year)

    # Default empty response
    rating_data = {
        "rating": None,
        "page_url": "",
        "backdrop_url": "",
        "backdrop_url_hd": "",
    }

    if result is None:
        _set_cached(cache_key, rating_data)
        return rating_data

    # Validate year match to ensure correct movie
    result_year = result.get("year")
    if not _is_year_match(year, result_year):
        _set_cached(cache_key, rating_data)
        return rating_data

    backdrop_path = result.get("backdrop_path")
    rating_data = {
        "rating": (
            round(float(result.get("vote_average", 0)), 1)
            if result.get("vote_average")
            else None
        ),
        "page_url": (
            f"https://www.themoviedb.org/movie/{result['id']}"
            if result.get("id")
            else ""
        ),
        "backdrop_url": (
            f"https://image.tmdb.org/t/p/w780{backdrop_path}" if backdrop_path else ""
        ),
        "backdrop_url_hd": (
            f"https://image.tmdb.org/t/p/original{backdrop_path}"
            if backdrop_path
            else ""
        ),
    }

    _set_cached(cache_key, rating_data)
    return rating_data


def fetch_rt_rating(title: str, year: int = None) -> dict:
    """
    Fetch Rotten Tomatoes rating by title with year validation.
    Returns: { rating, page_url } or { rating: None, ... }
    """
    cache_key = f"rt_rating:{title}:{year}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    result = fetch_movie_data_from_rt(title, year)

    # Default empty response
    rating_data = {
        "rating": None,
        "page_url": result.get("page_url", "") if result else "",
    }

    if result is None or result.get("rating", 0) == 0:
        _set_cached(cache_key, rating_data)
        return rating_data

    # Validate year match to ensure correct movie
    result_year = result.get("year")
    if not _is_year_match(year, result_year):
        _set_cached(cache_key, rating_data)
        return rating_data

    rating_data = {
        "rating": round(float(result["rating"]), 1),
        "page_url": result.get("page_url", ""),
    }

    _set_cached(cache_key, rating_data)
    return rating_data


def search_movies_parallel(queries: list) -> dict:
    """
    Search for multiple movies in parallel (metadata only, no ratings).
    Returns dict with 'movies' list and 'errors' list.
    """
    movies = []
    errors = []

    # Parse all queries first
    parsed_queries = []
    for q in queries:
        query_str = q.get("query", "") if isinstance(q, dict) else str(q)
        parsed = parse_movie_query(query_str)
        if parsed:
            parsed_queries.append(parsed)
        else:
            errors.append({"query": query_str, "error": "Empty query"})

    # Search all movies in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {
            executor.submit(search_movie, pq["query"]): pq for pq in parsed_queries
        }
        for future in as_completed(future_to_query):
            pq = future_to_query[future]
            try:
                movie_data = future.result()
                if movie_data:
                    movies.append(movie_data)
                else:
                    errors.append({"query": pq["query"], "error": "Movie not found"})
            except Exception as e:
                errors.append({"query": pq["query"], "error": str(e)})

    return {"movies": movies, "errors": errors}


def parse_movie_query(query: str) -> dict:
    """Parse a movie search query to extract title and year."""
    query = query.replace("\r", "").strip()
    if not query:
        return None

    year = 0
    title = query
    regex_to_find_year = r"1[89][0-9][0-9]|2[0-9][0-9][0-9]"
    match_year = re.search(regex_to_find_year, query)
    if match_year:
        year = int(match_year[0])
        title = re.sub(regex_to_find_year, "", query).strip()

    return {"query": query, "title": title, "year": year}
