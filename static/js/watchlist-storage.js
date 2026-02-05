// Watchlist Storage - API-based CRUD operations for logged-in users

const WatchlistStorage = {
  // Cache of movie IDs in watchlist for quick lookup
  _cachedIds: new Set(),
  _cacheLoaded: false,

  /**
   * Load watchlist movie IDs into cache for quick lookup
   * Call this after auth check on page load
   */
  async loadIds() {
    try {
      const response = await fetch('/api/watchlist?per_page=1000');
      if (response.status === 401) {
        this._cachedIds.clear();
        this._cacheLoaded = true;
        return;
      }
      if (response.ok) {
        const data = await response.json();
        this._cachedIds = new Set(data.movies.map(m => m.id));
        this._cacheLoaded = true;
      }
    } catch (error) {
      console.error('Error loading watchlist IDs:', error);
    }
  },

  /**
   * Check if a movie is in the watchlist (sync, uses cache)
   */
  has(movieId) {
    return this._cachedIds.has(movieId);
  },

  /**
   * Get all movies in the user's watchlist with optional filters
   * @param {Object} options - Filter, sort, and pagination options
   * @returns {Promise<Object>} - { movies, total, page, per_page, pages }
   */
  async getAll(options = {}) {
    const params = new URLSearchParams();

    if (options.genre) params.append("genre", options.genre);
    if (options.year_start) params.append("year_start", options.year_start);
    if (options.year_end) params.append("year_end", options.year_end);
    if (options.min_rating) params.append("min_rating", options.min_rating);
    if (options.search) params.append("search", options.search);
    if (options.sort_by) params.append("sort_by", options.sort_by);
    if (options.sort_order) params.append("sort_order", options.sort_order);
    if (options.page) params.append("page", options.page);
    if (options.per_page) params.append("per_page", options.per_page);

    const url = `/api/watchlist${params.toString() ? "?" + params.toString() : ""}`;

    try {
      const response = await fetch(url);

      if (response.status === 401) {
        // User not logged in
        return { movies: [], total: 0, page: 1, per_page: 50, pages: 0, error: "unauthorized" };
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching watchlist:", error);
      return { movies: [], total: 0, page: 1, per_page: 50, pages: 0, error: error.message };
    }
  },

  /**
   * Add a movie to the watchlist
   * @param {Object} movie - Movie data from ranklist
   * @returns {Promise<Object>} - { success, movie, error }
   */
  async add(movie) {
    try {
      const response = await fetch("/api/watchlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          movie_id: movie.id,
          title: movie.title,
          year: movie.year,
          logo_url: movie.logo_url,
          backdrop_url: movie.backdrop_url,
          backdrop_url_hd: movie.backdrop_url_hd,
          imdb_rating: movie.imdb?.rating,
          imdb_page_url: movie.imdb?.page_url,
          tmdb_rating: movie.tmdb?.rating,
          tmdb_page_url: movie.tmdb?.page_url,
          rt_tomatometer: movie.rt?.tomatometer || movie.rt?.rating,
          rt_popcornmeter: movie.rt?.popcornmeter,
          rt_page_url: movie.rt?.page_url,
          genres: movie.genres,
        }),
      });

      if (response.status === 401) {
        return { success: false, error: "Please log in to add to watchlist" };
      }

      const data = await response.json();
      if (data.success) {
        this._cachedIds.add(movie.id);
      }
      return data;
    } catch (error) {
      console.error("Error adding to watchlist:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Remove a movie from the watchlist
   * @param {string} movieId - The movie's IMDB ID
   * @returns {Promise<Object>} - { success, error }
   */
  async remove(movieId) {
    try {
      const response = await fetch(`/api/watchlist/${encodeURIComponent(movieId)}`, {
        method: "DELETE",
      });

      if (response.status === 401) {
        return { success: false, error: "Please log in" };
      }

      const data = await response.json();
      if (data.success) {
        this._cachedIds.delete(movieId);
      }
      return data;
    } catch (error) {
      console.error("Error removing from watchlist:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Add multiple movies to the watchlist at once
   * @param {Array} movies - Array of movie data objects
   * @returns {Promise<Object>} - { success, added, added_count, skipped, skipped_count, errors }
   */
  async addBulk(movies) {
    try {
      const moviesData = movies.map((movie) => ({
        movie_id: movie.id,
        title: movie.title,
        year: movie.year,
        logo_url: movie.logo_url,
        backdrop_url: movie.backdrop_url,
        backdrop_url_hd: movie.backdrop_url_hd,
        imdb_rating: movie.imdb?.rating,
        imdb_page_url: movie.imdb?.page_url,
        tmdb_rating: movie.tmdb?.rating,
        tmdb_page_url: movie.tmdb?.page_url,
        rt_tomatometer: movie.rt?.tomatometer || movie.rt?.rating,
        rt_popcornmeter: movie.rt?.popcornmeter,
        rt_page_url: movie.rt?.page_url,
        genres: movie.genres,
      }));

      const response = await fetch("/api/watchlist/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ movies: moviesData }),
      });

      if (response.status === 401) {
        return { success: false, error: "Please log in to add to watchlist" };
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error bulk adding to watchlist:", error);
      return { success: false, error: error.message };
    }
  },

  /**
   * Get all unique genres in user's watchlist for filter dropdown
   * @returns {Promise<Array>} - Array of genre strings
   */
  async getGenres() {
    try {
      const response = await fetch("/api/watchlist/genres");

      if (response.status === 401) {
        return [];
      }

      const data = await response.json();
      return data.genres || [];
    } catch (error) {
      console.error("Error fetching genres:", error);
      return [];
    }
  },

  /**
   * Check if a movie is in the user's watchlist
   * @param {string} movieId - The movie's IMDB ID
   * @param {Array} watchlistMovies - Optional cached watchlist movies
   * @returns {boolean}
   */
  isInWatchlist(movieId, watchlistMovies = null) {
    if (watchlistMovies) {
      return watchlistMovies.some((m) => m.id === movieId);
    }
    // If no cache provided, return false (caller should check with getAll first)
    return false;
  },
};
