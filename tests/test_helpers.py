"""Tests for helper functions with mocked API calls."""

from unittest.mock import patch


class TestYearValidation:
    """Tests for year validation helper."""

    def test_exact_year_match(self):
        """Test exact year match passes."""
        from utils.helpers import _is_year_match

        assert _is_year_match(2019, 2019) is True

    def test_year_within_tolerance(self):
        """Test years within ±1 tolerance pass."""
        from utils.helpers import _is_year_match

        assert _is_year_match(2019, 2020) is True
        assert _is_year_match(2019, 2018) is True

    def test_year_outside_tolerance(self):
        """Test years outside tolerance fail."""
        from utils.helpers import _is_year_match

        assert _is_year_match(2019, 2021) is False
        assert _is_year_match(2019, 2017) is False

    def test_missing_expected_year_skips_validation(self):
        """Test missing expected year skips validation."""
        from utils.helpers import _is_year_match

        assert _is_year_match(None, 2019) is True
        assert _is_year_match(0, 2019) is True

    def test_missing_actual_year_skips_validation(self):
        """Test missing actual year skips validation."""
        from utils.helpers import _is_year_match

        assert _is_year_match(2019, None) is True
        assert _is_year_match(2019, 0) is True

    def test_custom_tolerance(self):
        """Test custom tolerance value."""
        from utils.helpers import _is_year_match

        assert _is_year_match(2019, 2021, tolerance=2) is True
        assert _is_year_match(2019, 2022, tolerance=2) is False


class TestSearchMovie:
    """Tests for movie search with mocked IMDB API."""

    @patch("utils.helpers.search_imdb")
    def test_search_movie_success(self, mock_search_imdb):
        """Test successful movie search."""
        from utils.helpers import search_movie

        mock_search_imdb.return_value = {
            "id": "tt0133093",
            "title": "The Matrix",
            "year": 1999,
            "image_url": "https://example.com/matrix.jpg",
            "page_url": "https://imdb.com/title/tt0133093/",
        }

        result = search_movie("The Matrix 1999")

        assert result is not None
        assert result["id"] == "tt0133093"
        assert result["title"] == "The Matrix"
        assert result["year"] == 1999
        assert result["query"] == "The Matrix 1999"
        mock_search_imdb.assert_called_once_with("The Matrix 1999")

    @patch("utils.helpers.search_imdb")
    def test_search_movie_not_found(self, mock_search_imdb):
        """Test movie not found returns None."""
        from utils.helpers import search_movie

        mock_search_imdb.return_value = None

        result = search_movie("Nonexistent Movie 2099")

        assert result is None

    @patch("utils.helpers.search_imdb")
    def test_search_movie_caching(self, mock_search_imdb):
        """Test search results are cached."""
        from utils.helpers import _cache, search_movie

        # Clear cache first
        _cache.clear()

        mock_search_imdb.return_value = {
            "id": "tt0133093",
            "title": "The Matrix",
            "year": 1999,
            "image_url": "https://example.com/matrix.jpg",
            "page_url": "https://imdb.com/title/tt0133093/",
        }

        # First call - should hit API
        result1 = search_movie("The Matrix 1999")
        # Second call - should use cache
        result2 = search_movie("The Matrix 1999")

        assert result1 == result2
        # API should only be called once due to caching
        assert mock_search_imdb.call_count == 1


class TestFetchImdbRating:
    """Tests for IMDB rating fetch with mocked API."""

    @patch("utils.helpers.get_imdb_rating")
    def test_fetch_imdb_rating_success(self, mock_get_rating):
        """Test successful IMDB rating fetch."""
        from utils.helpers import _cache, fetch_imdb_rating

        _cache.clear()

        mock_get_rating.return_value = {
            "rating": 8.7,
            "page_url": "https://imdb.com/title/tt0133093/",
        }

        result = fetch_imdb_rating("tt0133093")

        assert result["rating"] == 8.7
        assert "imdb.com" in result["page_url"]

    @patch("utils.helpers.get_imdb_rating")
    def test_fetch_imdb_rating_not_found(self, mock_get_rating):
        """Test IMDB rating not found returns default."""
        from utils.helpers import _cache, fetch_imdb_rating

        _cache.clear()

        mock_get_rating.return_value = None

        result = fetch_imdb_rating("tt9999999")

        assert result["rating"] is None
        assert "tt9999999" in result["page_url"]


class TestFetchTmdbRating:
    """Tests for TMDB rating fetch with mocked API."""

    @patch("utils.helpers.fetch_movie_data_from_tmdb")
    def test_fetch_tmdb_rating_success(self, mock_fetch_tmdb):
        """Test successful TMDB rating fetch."""
        from utils.helpers import _cache, fetch_tmdb_rating

        _cache.clear()

        mock_fetch_tmdb.return_value = {
            "id": 603,
            "vote_average": 8.2,
            "backdrop_path": "/backdrop.jpg",
            "year": 1999,
        }

        result = fetch_tmdb_rating("The Matrix", 1999)

        assert result["rating"] == 8.2
        assert "themoviedb.org/movie/603" in result["page_url"]
        assert "backdrop.jpg" in result["backdrop_url"]

    @patch("utils.helpers.fetch_movie_data_from_tmdb")
    def test_fetch_tmdb_rating_not_found(self, mock_fetch_tmdb):
        """Test TMDB rating not found returns empty."""
        from utils.helpers import _cache, fetch_tmdb_rating

        _cache.clear()

        mock_fetch_tmdb.return_value = None

        result = fetch_tmdb_rating("Nonexistent Movie", 2099)

        assert result["rating"] is None
        assert result["page_url"] == ""

    @patch("utils.helpers.fetch_movie_data_from_tmdb")
    def test_fetch_tmdb_rating_year_mismatch(self, mock_fetch_tmdb):
        """Test TMDB rating with year mismatch returns empty."""
        from utils.helpers import _cache, fetch_tmdb_rating

        _cache.clear()

        # API returns 2019 movie but we're searching for 2024
        mock_fetch_tmdb.return_value = {
            "id": 475557,
            "vote_average": 8.4,
            "backdrop_path": "/backdrop.jpg",
            "year": 2019,
        }

        result = fetch_tmdb_rating("Joker", 2024)

        # Should return empty due to year mismatch (2024 vs 2019 = 5 years diff)
        assert result["rating"] is None

    @patch("utils.helpers.fetch_movie_data_from_tmdb")
    def test_fetch_tmdb_rating_year_within_tolerance(self, mock_fetch_tmdb):
        """Test TMDB rating with year within tolerance succeeds."""
        from utils.helpers import _cache, fetch_tmdb_rating

        _cache.clear()

        mock_fetch_tmdb.return_value = {
            "id": 475557,
            "vote_average": 8.4,
            "backdrop_path": "/backdrop.jpg",
            "year": 2019,
        }

        # 2020 is within ±1 tolerance of 2019
        result = fetch_tmdb_rating("Joker", 2020)

        assert result["rating"] == 8.4


class TestFetchRtRating:
    """Tests for Rotten Tomatoes rating fetch with mocked API."""

    @patch("utils.helpers.fetch_movie_data_from_rt")
    def test_fetch_rt_rating_success(self, mock_fetch_rt):
        """Test successful RT rating fetch with tomatometer and popcornmeter."""
        from utils.helpers import _cache, fetch_rt_rating

        _cache.clear()

        mock_fetch_rt.return_value = {
            "rating": 6.8,
            "tomatometer": 6.8,
            "popcornmeter": 8.2,
            "page_url": "https://www.rottentomatoes.com/m/joker_2019",
            "year": 2019,
        }

        result = fetch_rt_rating("Joker", 2019)

        assert result["rating"] == 6.8
        assert result["tomatometer"] == 6.8
        assert result["popcornmeter"] == 8.2
        assert "rottentomatoes.com" in result["page_url"]

    @patch("utils.helpers.fetch_movie_data_from_rt")
    def test_fetch_rt_rating_not_found(self, mock_fetch_rt):
        """Test RT rating not found returns empty."""
        from utils.helpers import _cache, fetch_rt_rating

        _cache.clear()

        mock_fetch_rt.return_value = {
            "rating": 0,
            "tomatometer": 0,
            "popcornmeter": 0,
            "page_url": "",
            "year": None,
        }

        result = fetch_rt_rating("Nonexistent Movie", 2099)

        assert result["rating"] is None
        assert result["tomatometer"] is None
        assert result["popcornmeter"] is None

    @patch("utils.helpers.fetch_movie_data_from_rt")
    def test_fetch_rt_rating_year_mismatch(self, mock_fetch_rt):
        """Test RT rating with year mismatch returns empty."""
        from utils.helpers import _cache, fetch_rt_rating

        _cache.clear()

        # Returns 2010 movie when searching for 2020
        mock_fetch_rt.return_value = {
            "rating": 8.7,
            "tomatometer": 8.7,
            "popcornmeter": 9.1,
            "page_url": "https://www.rottentomatoes.com/m/inception",
            "year": 2010,
        }

        result = fetch_rt_rating("Inception", 2020)

        # Should return empty due to year mismatch (10 years diff)
        assert result["rating"] is None
        assert result["tomatometer"] is None
        assert result["popcornmeter"] is None


class TestSearchMoviesParallel:
    """Tests for parallel movie search with mocked API."""

    @patch("utils.helpers.search_movie")
    def test_search_movies_parallel_success(self, mock_search):
        """Test successful parallel search."""
        from utils.helpers import search_movies_parallel

        mock_search.side_effect = [
            {
                "id": "tt0133093",
                "query": "The Matrix 1999",
                "title": "The Matrix",
                "year": 1999,
                "logo_url": "https://example.com/matrix.jpg",
            },
            {
                "id": "tt1375666",
                "query": "Inception 2010",
                "title": "Inception",
                "year": 2010,
                "logo_url": "https://example.com/inception.jpg",
            },
        ]

        result = search_movies_parallel(
            [{"query": "The Matrix 1999"}, {"query": "Inception 2010"}]
        )

        assert len(result["movies"]) == 2
        assert len(result["errors"]) == 0

    @patch("utils.helpers.search_movie")
    def test_search_movies_parallel_partial_failure(self, mock_search):
        """Test parallel search with some failures."""
        from utils.helpers import search_movies_parallel

        mock_search.side_effect = [
            {
                "id": "tt0133093",
                "query": "The Matrix 1999",
                "title": "The Matrix",
                "year": 1999,
                "logo_url": "https://example.com/matrix.jpg",
            },
            None,  # Second movie not found
        ]

        result = search_movies_parallel(
            [{"query": "The Matrix 1999"}, {"query": "Nonexistent 2099"}]
        )

        assert len(result["movies"]) == 1
        assert len(result["errors"]) == 1
        assert result["movies"][0]["title"] == "The Matrix"

    def test_search_movies_parallel_empty_query(self):
        """Test parallel search with empty query."""
        from utils.helpers import search_movies_parallel

        result = search_movies_parallel([{"query": ""}, {"query": "   "}])

        assert len(result["movies"]) == 0
        assert len(result["errors"]) == 2


class TestParseMovieQuery:
    """Tests for movie query parsing."""

    def test_parse_with_year(self):
        """Test parsing query with year."""
        from utils.helpers import parse_movie_query

        result = parse_movie_query("The Matrix 1999")

        assert result["query"] == "The Matrix 1999"
        assert result["title"] == "The Matrix"
        assert result["year"] == 1999

    def test_parse_without_year(self):
        """Test parsing query without year."""
        from utils.helpers import parse_movie_query

        result = parse_movie_query("The Matrix")

        assert result["query"] == "The Matrix"
        assert result["title"] == "The Matrix"
        assert result["year"] == 0

    def test_parse_empty_query(self):
        """Test parsing empty query returns None."""
        from utils.helpers import parse_movie_query

        assert parse_movie_query("") is None
        assert parse_movie_query("   ") is None

    def test_parse_with_carriage_return(self):
        """Test parsing strips carriage returns."""
        from utils.helpers import parse_movie_query

        result = parse_movie_query("The Matrix 1999\r")

        assert result["query"] == "The Matrix 1999"
        assert result["year"] == 1999
