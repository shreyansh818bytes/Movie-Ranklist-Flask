"""Tests for API modules with mocked HTTP requests."""

import json
from unittest.mock import MagicMock, patch


class TestRottenTomatoesAPI:
    """Tests for Rotten Tomatoes scraper with mocked requests."""

    @patch("utils.api.rt.requests.get")
    def test_fetch_rt_with_year_suffix(self, mock_get):
        """Test RT fetches year-suffixed URL first when year provided."""
        from utils.api.rt import fetch_movie_data_from_rt

        # Mock successful response for year-suffixed URL
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <script type="application/ld+json">
        {
            "@type": "Movie",
            "name": "Joker",
            "dateCreated": "2019-10-04",
            "aggregateRating": {"ratingValue": 68}
        }
        </script>
        </html>
        """
        mock_get.return_value = mock_response

        result = fetch_movie_data_from_rt("Joker", 2019)

        assert result["rating"] == 6.8
        assert result["year"] == 2019
        assert "joker_2019" in result["page_url"]
        # Should have tried the year-suffixed URL
        mock_get.assert_called_with(
            "https://www.rottentomatoes.com/m/joker_2019",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=10,
        )

    @patch("utils.api.rt.requests.get")
    def test_fetch_rt_fallback_to_title_only(self, mock_get):
        """Test RT falls back to title-only URL when year-suffixed fails."""
        from utils.api.rt import fetch_movie_data_from_rt

        def mock_get_side_effect(url, **kwargs):
            response = MagicMock()
            if "_2019" in url:
                # Year-suffixed URL returns 404
                response.status_code = 404
                response.text = ""
            else:
                # Title-only URL works
                response.status_code = 200
                response.text = """
                <html>
                <script type="application/ld+json">
                {
                    "@type": "Movie",
                    "name": "Inception",
                    "dateCreated": "2010-07-16",
                    "aggregateRating": {"ratingValue": 87}
                }
                </script>
                </html>
                """
            return response

        mock_get.side_effect = mock_get_side_effect

        result = fetch_movie_data_from_rt("Inception", 2019)

        assert result["rating"] == 8.7
        assert result["year"] == 2010
        assert mock_get.call_count == 2  # Tried both URLs

    @patch("utils.api.rt.requests.get")
    def test_fetch_rt_without_year(self, mock_get):
        """Test RT fetches title-only URL when no year provided."""
        from utils.api.rt import fetch_movie_data_from_rt

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <script type="application/ld+json">
        {
            "@type": "Movie",
            "name": "Inception",
            "dateCreated": "2010-07-16",
            "aggregateRating": {"ratingValue": 87}
        }
        </script>
        </html>
        """
        mock_get.return_value = mock_response

        result = fetch_movie_data_from_rt("Inception")

        assert result["rating"] == 8.7
        assert "inception" in result["page_url"]
        assert "_" not in result["page_url"].split("/")[-1]  # No year suffix

    @patch("utils.api.rt.requests.get")
    def test_fetch_rt_no_rating(self, mock_get):
        """Test RT returns zero rating when no aggregate rating found."""
        from utils.api.rt import fetch_movie_data_from_rt

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <script type="application/ld+json">
        {
            "@type": "Movie",
            "name": "Some Movie"
        }
        </script>
        </html>
        """
        mock_get.return_value = mock_response

        result = fetch_movie_data_from_rt("Some Movie")

        assert result["rating"] == 0.0

    @patch("utils.api.rt.requests.get")
    def test_fetch_rt_404(self, mock_get):
        """Test RT returns empty result on 404."""
        from utils.api.rt import fetch_movie_data_from_rt

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = fetch_movie_data_from_rt("Nonexistent Movie")

        assert result["rating"] == 0.0
        assert result["page_url"] == ""

    @patch("utils.api.rt.requests.get")
    def test_fetch_rt_request_exception(self, mock_get):
        """Test RT handles request exceptions gracefully."""
        import requests

        from utils.api.rt import fetch_movie_data_from_rt

        mock_get.side_effect = requests.exceptions.Timeout()

        result = fetch_movie_data_from_rt("Some Movie")

        assert result["rating"] == 0.0
        assert result["page_url"] == ""


class TestTitleToSlug:
    """Tests for RT title to slug conversion."""

    def test_simple_title(self):
        """Test simple title conversion."""
        from utils.api.rt import _title_to_slug

        assert _title_to_slug("Inception") == "inception"

    def test_title_with_spaces(self):
        """Test title with spaces."""
        from utils.api.rt import _title_to_slug

        assert _title_to_slug("The Matrix") == "the_matrix"

    def test_title_with_punctuation(self):
        """Test title with punctuation removed."""
        from utils.api.rt import _title_to_slug

        assert _title_to_slug("Spider-Man: No Way Home") == "spiderman_no_way_home"

    def test_title_with_apostrophe(self):
        """Test title with apostrophe removed."""
        from utils.api.rt import _title_to_slug

        assert _title_to_slug("Ocean's Eleven") == "oceans_eleven"


class TestTmdbAPI:
    """Tests for TMDb API with mocked requests."""

    @patch("utils.api.tmdb.requests.get")
    def test_fetch_tmdb_success(self, mock_get):
        """Test successful TMDb fetch."""
        from utils.api.tmdb import fetch_movie_data_from_tmdb

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": 603,
                    "title": "The Matrix",
                    "vote_average": 8.2,
                    "release_date": "1999-03-30",
                    "backdrop_path": "/backdrop.jpg",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = fetch_movie_data_from_tmdb("The Matrix", 1999)

        assert result is not None
        assert result["id"] == 603
        assert result["vote_average"] == 8.2
        assert result["year"] == 1999

    @patch("utils.api.tmdb.requests.get")
    def test_fetch_tmdb_no_results(self, mock_get):
        """Test TMDb returns None when no results."""
        from utils.api.tmdb import fetch_movie_data_from_tmdb

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = fetch_movie_data_from_tmdb("Nonexistent Movie", 2099)

        assert result is None

    @patch("utils.api.tmdb.requests.get")
    def test_fetch_tmdb_extracts_year(self, mock_get):
        """Test TMDb extracts year from release_date."""
        from utils.api.tmdb import fetch_movie_data_from_tmdb

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": 475557,
                    "title": "Joker",
                    "vote_average": 8.4,
                    "release_date": "2019-10-04",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = fetch_movie_data_from_tmdb("Joker", 2019)

        assert result["year"] == 2019

    @patch("utils.api.tmdb.requests.get")
    def test_fetch_tmdb_missing_release_date(self, mock_get):
        """Test TMDb handles missing release_date."""
        from utils.api.tmdb import fetch_movie_data_from_tmdb

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": 12345,
                    "title": "Unknown Movie",
                    "vote_average": 5.0,
                    "release_date": "",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = fetch_movie_data_from_tmdb("Unknown Movie", None)

        assert result["year"] is None

    @patch("utils.api.tmdb.requests.get")
    def test_fetch_tmdb_includes_year_param(self, mock_get):
        """Test TMDb includes year in API params when provided."""
        from utils.api.tmdb import fetch_movie_data_from_tmdb

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        fetch_movie_data_from_tmdb("The Matrix", 1999)

        call_args = mock_get.call_args
        assert call_args[1]["params"]["year"] == 1999

    @patch("utils.api.tmdb.requests.get")
    def test_fetch_tmdb_no_year_param_when_none(self, mock_get):
        """Test TMDb excludes year param when not provided."""
        from utils.api.tmdb import fetch_movie_data_from_tmdb

        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        fetch_movie_data_from_tmdb("The Matrix", None)

        call_args = mock_get.call_args
        assert "year" not in call_args[1]["params"]


class TestMovieRatingEndpoints:
    """Tests for movie rating API endpoints."""

    def test_get_imdb_rating(self, client):
        """Test IMDB rating endpoint with mocked API."""
        with patch("app.fetch_imdb_rating") as mock_fetch:
            mock_fetch.return_value = {
                "rating": 8.7,
                "page_url": "https://imdb.com/title/tt0133093/",
            }

            response = client.get("/api/movies/tt0133093/rating/imdb")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["rating"] == 8.7

    def test_get_tmdb_rating(self, client):
        """Test TMDb rating endpoint with mocked API."""
        with patch("app.fetch_tmdb_rating") as mock_fetch:
            mock_fetch.return_value = {
                "rating": 8.2,
                "page_url": "https://themoviedb.org/movie/603",
                "backdrop_url": "https://image.tmdb.org/t/p/w780/backdrop.jpg",
                "backdrop_url_hd": "https://image.tmdb.org/t/p/original/backdrop.jpg",
            }

            response = client.get(
                "/api/movies/tt0133093/rating/tmdb?title=The%20Matrix&year=1999"
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["rating"] == 8.2
            mock_fetch.assert_called_with("The Matrix", 1999)

    def test_get_tmdb_rating_missing_title(self, client):
        """Test TMDb rating endpoint requires title."""
        response = client.get("/api/movies/tt0133093/rating/tmdb")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Title is required" in data["error"]

    def test_get_rt_rating(self, client):
        """Test RT rating endpoint with mocked API."""
        with patch("app.fetch_rt_rating") as mock_fetch:
            mock_fetch.return_value = {
                "rating": 8.7,
                "page_url": "https://rottentomatoes.com/m/the_matrix",
            }

            response = client.get(
                "/api/movies/tt0133093/rating/rt?title=The%20Matrix&year=1999"
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["rating"] == 8.7
            mock_fetch.assert_called_with("The Matrix", 1999)

    def test_get_rt_rating_missing_title(self, client):
        """Test RT rating endpoint requires title."""
        response = client.get("/api/movies/tt0133093/rating/rt")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Title is required" in data["error"]

    def test_get_rating_unknown_platform(self, client):
        """Test rating endpoint with unknown platform."""
        response = client.get("/api/movies/tt0133093/rating/unknown")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Unknown platform" in data["error"]


class TestMovieSearchEndpoint:
    """Tests for movie search API endpoint."""

    def test_search_movies_success(self, client):
        """Test successful movie search."""
        with patch("app.search_movies_parallel") as mock_search:
            mock_search.return_value = {
                "movies": [
                    {
                        "id": "tt0133093",
                        "query": "The Matrix 1999",
                        "title": "The Matrix",
                        "year": 1999,
                        "logo_url": "https://example.com/matrix.jpg",
                    }
                ],
                "errors": [],
            }

            response = client.post(
                "/api/movies/search",
                data=json.dumps({"movies": [{"query": "The Matrix 1999"}]}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data["movies"]) == 1
            assert data["movies"][0]["title"] == "The Matrix"

    def test_search_movies_missing_movies_key(self, client):
        """Test search endpoint requires movies key."""
        response = client.post(
            "/api/movies/search",
            data=json.dumps({"queries": []}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "movies" in data["error"]

    def test_search_movies_invalid_movies_type(self, client):
        """Test search endpoint requires movies to be array."""
        response = client.post(
            "/api/movies/search",
            data=json.dumps({"movies": "not an array"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "array" in data["error"]
