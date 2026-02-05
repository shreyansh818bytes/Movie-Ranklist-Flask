// Watchlist Renderer - Grid layout with filters and movie cards

const WatchlistRenderer = {
  // Current filter/sort state
  state: {
    genre: "",
    yearStart: "",
    yearEnd: "",
    minRating: "",
    search: "",
    sortBy: "imdb",
    sortOrder: "desc",
    page: 1,
    perPage: 50,
  },

  // Cached data
  genres: [],
  movies: [],
  total: 0,

  getContainer() {
    return document.getElementById("watchlist-grid");
  },

  getFiltersContainer() {
    return document.getElementById("watchlist-filters");
  },

  /**
   * Initialize the watchlist view
   */
  async init() {
    // Load genres for filter dropdown
    this.genres = await WatchlistStorage.getGenres();
    this.renderFilters();
    this.setupFilterListeners();
    await this.loadAndRender();
  },

  /**
   * Render the filter bar
   */
  renderFilters() {
    const container = this.getFiltersContainer();
    if (!container) return;

    // Build genre options
    const genreOptions = this.genres
      .map((g) => `<option value="${g}">${g}</option>`)
      .join("");

    // Build decade options (1950s to 2020s)
    const currentDecade = Math.floor(new Date().getFullYear() / 10) * 10;
    let decadeOptions = '<option value="">All Decades</option>';
    for (let decade = currentDecade; decade >= 1950; decade -= 10) {
      decadeOptions += `<option value="${decade}">${decade}s</option>`;
    }

    container.innerHTML = `
      <div class="filter-bar">
        <div class="filter-group">
          <select id="filter-genre" class="filter-select" title="Filter by genre">
            <option value="">All Genres</option>
            ${genreOptions}
          </select>
        </div>

        <div class="filter-group">
          <select id="filter-decade" class="filter-select" title="Filter by decade">
            ${decadeOptions}
          </select>
        </div>

        <div class="filter-group">
          <select id="filter-rating" class="filter-select" title="Minimum rating">
            <option value="">Any Rating</option>
            <option value="9">9+</option>
            <option value="8">8+</option>
            <option value="7">7+</option>
            <option value="6">6+</option>
          </select>
        </div>

        <div class="filter-group search-group">
          <div class="search-input-wrapper">
            <i class="fa fa-search search-icon"></i>
            <input type="text" id="filter-search" class="filter-input" placeholder="Filter by movie name..." />
          </div>
        </div>

        <div class="filter-group sort-group">
          <select id="filter-sort" class="filter-select" title="Sort by">
            <option value="imdb:desc">IMDb Rating (High-Low)</option>
            <option value="imdb:asc">IMDb Rating (Low-High)</option>
            <option value="added_at:desc">Recently Added</option>
            <option value="added_at:asc">Oldest Added</option>
            <option value="rt_tomatometer:desc">Tomatometer (High-Low)</option>
            <option value="rt_popcornmeter:desc">Popcornmeter (High-Low)</option>
            <option value="year:desc">Year (New-Old)</option>
            <option value="year:asc">Year (Old-New)</option>
            <option value="title:asc">Title (A-Z)</option>
          </select>
        </div>
      </div>
    `;
  },

  /**
   * Setup event listeners for filters
   */
  setupFilterListeners() {
    const genreSelect = document.getElementById("filter-genre");
    const decadeSelect = document.getElementById("filter-decade");
    const ratingSelect = document.getElementById("filter-rating");
    const searchInput = document.getElementById("filter-search");
    const sortSelect = document.getElementById("filter-sort");

    if (genreSelect) {
      genreSelect.addEventListener("change", () => {
        this.state.genre = genreSelect.value;
        this.state.page = 1;
        this.loadAndRender();
      });
    }

    if (decadeSelect) {
      decadeSelect.addEventListener("change", () => {
        if (decadeSelect.value) {
          this.state.yearStart = parseInt(decadeSelect.value);
          this.state.yearEnd = parseInt(decadeSelect.value) + 9;
        } else {
          this.state.yearStart = "";
          this.state.yearEnd = "";
        }
        this.state.page = 1;
        this.loadAndRender();
      });
    }

    if (ratingSelect) {
      ratingSelect.addEventListener("change", () => {
        this.state.minRating = ratingSelect.value;
        this.state.page = 1;
        this.loadAndRender();
      });
    }

    if (searchInput) {
      let searchTimeout;
      searchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          this.state.search = searchInput.value;
          this.state.page = 1;
          this.loadAndRender();
        }, 300);
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener("change", () => {
        const [sortBy, sortOrder] = sortSelect.value.split(":");
        this.state.sortBy = sortBy;
        this.state.sortOrder = sortOrder || "desc";
        this.state.page = 1;
        this.loadAndRender();
      });
    }
  },

  /**
   * Load movies from API and render the grid
   */
  async loadAndRender() {
    const container = this.getContainer();
    if (!container) return;

    // Show loading state
    container.innerHTML = '<div class="watchlist-loading"><i class="fa fa-spinner fa-spin"></i> Loading watchlist...</div>';

    const result = await WatchlistStorage.getAll({
      genre: this.state.genre,
      year_start: this.state.yearStart,
      year_end: this.state.yearEnd,
      min_rating: this.state.minRating,
      search: this.state.search,
      sort_by: this.state.sortBy,
      sort_order: this.state.sortOrder,
      page: this.state.page,
      per_page: this.state.perPage,
    });

    if (result.error === "unauthorized") {
      container.innerHTML = `
        <div class="watchlist-empty">
          <i class="fa fa-lock"></i>
          <p>Please <a href="/login">log in</a> to view your watchlist</p>
        </div>
      `;
      return;
    }

    this.movies = result.movies || [];
    this.total = result.total || 0;

    this.render();
    this.updateCount();
  },

  /**
   * Render the movie grid
   */
  render() {
    const container = this.getContainer();
    if (!container) return;

    if (this.movies.length === 0) {
      container.innerHTML = `
        <div class="watchlist-empty">
          <i class="fa fa-film"></i>
          <p>Your watchlist is empty</p>
          <p class="text-muted">Add movies from your ranklist to get started!</p>
        </div>
      `;
      return;
    }

    container.innerHTML = "";
    this.movies.forEach((movie) => {
      const card = this.createMovieCard(movie);
      container.appendChild(card);
    });
  },

  /**
   * Create a movie card element
   * @param {Object} movie - Movie data
   * @returns {HTMLElement}
   */
  createMovieCard(movie) {
    const card = document.createElement("div");
    card.className = "watchlist-card";
    card.id = `watchlist-${movie.id}`;

    // Build rating pills HTML
    let ratingPills = "";
    if (movie.imdb_rating) {
      const imdbUrl = movie.imdb_page_url || `https://www.imdb.com/title/${movie.id}/`;
      ratingPills += `
        <a href="${imdbUrl}" target="_blank" rel="noopener noreferrer" class="icon-text-pill" title="IMDb">
          <img src="/static/assets/imdb-icon.svg" alt="IMDb" />
          <p>${movie.imdb_rating}</p>
        </a>`;
    }
    if (movie.tmdb_rating) {
      const tmdbUrl = movie.tmdb_page_url || `https://www.themoviedb.org/movie/${movie.id}`;
      ratingPills += `
        <a href="${tmdbUrl}" target="_blank" rel="noopener noreferrer" class="icon-text-pill" title="TMDB">
          <img src="/static/assets/tmdb-icon.svg" alt="TMDB" />
          <p>${movie.tmdb_rating}</p>
        </a>`;
    }
    if (movie.rt_tomatometer) {
      ratingPills += `
        <a href="${movie.rt_page_url || "#"}" target="_blank" rel="noopener noreferrer" class="icon-text-pill rt-tomato" title="Tomatometer (Critics)">
          <img src="/static/assets/rt-icon.svg" alt="RT" />
          <p>${movie.rt_tomatometer}</p>
        </a>`;
    }
    if (movie.rt_popcornmeter) {
      ratingPills += `
        <span class="icon-text-pill rt-popcorn" title="Popcornmeter (Audience)">
          <i class="fa fa-ticket"></i>
          <p>${movie.rt_popcornmeter}</p>
        </span>`;
    }

    // Build genres HTML
    const genresHtml = movie.genres && movie.genres.length > 0
      ? movie.genres.slice(0, 3).map((g) => `<span class="genre-tag">${g}</span>`).join("")
      : "";

    card.innerHTML = `
      <div class="watchlist-card-poster">
        <img src="${movie.logo_url || "/static/assets/not-found-icon.svg"}" alt="${movie.title}" loading="lazy" />
        ${movie.average_score ? `<div class="watchlist-card-score">${movie.average_score.toFixed(1)}</div>` : ""}
      </div>
      <div class="watchlist-card-info">
        <h4 class="watchlist-card-title" title="${movie.title}">${movie.title}</h4>
        <div class="watchlist-card-meta">
          <span class="year">${movie.year || "Unknown"}</span>
          ${genresHtml ? `<div class="genres">${genresHtml}</div>` : ""}
        </div>
        <div class="watchlist-card-ratings">
          ${ratingPills || '<span class="text-muted">No ratings</span>'}
        </div>
      </div>
      <button class="btn-quick-compare" onclick="WatchlistRenderer.addToRanklist('${movie.id}')" data-tooltip="Quick compare">
        <i class="fa fa-balance-scale"></i>
      </button>
    `;

    // Add backdrop on hover if available
    if (movie.backdrop_url) {
      card.style.setProperty("--backdrop-url", `url(${movie.backdrop_url})`);
      card.classList.add("has-backdrop");
    }

    return card;
  },

  /**
   * Update the movie count display
   */
  updateCount() {
    const countEl = document.getElementById("watchlist-count");
    if (countEl) {
      countEl.textContent = `${this.total} Movie${this.total !== 1 ? "s" : ""}`;
    }
  },

  /**
   * Remove a movie from the watchlist
   * @param {string} movieId
   */
  async removeMovie(movieId) {
    const card = document.getElementById(`watchlist-${movieId}`);
    if (card) {
      card.classList.add("card-removing");
    }

    const result = await WatchlistStorage.remove(movieId);

    if (result.success) {
      // Remove from local cache
      this.movies = this.movies.filter((m) => m.id !== movieId);
      this.total--;

      if (card) {
        card.addEventListener("animationend", () => {
          card.remove();
          if (this.movies.length === 0) {
            this.render();
          }
        });
      }

      this.updateCount();
      showToast("Removed from watchlist", "success");
    } else {
      if (card) {
        card.classList.remove("card-removing");
      }
      showToast(result.error || "Failed to remove movie", "error");
    }
  },

  /**
   * Add a movie to the ranklist for comparison
   * @param {string} movieId
   */
  addToRanklist(movieId) {
    const movie = this.movies.find((m) => m.id === movieId);
    if (!movie) return;

    // Convert watchlist movie format to ranklist format
    const ranklistMovie = {
      id: movie.id,
      query: movie.title,
      title: movie.title,
      year: movie.year,
      logo_url: movie.logo_url,
      backdrop_url: movie.backdrop_url,
      backdrop_url_hd: movie.backdrop_url_hd,
      average_score: movie.average_score || 0,
      imdb: {
        rating: movie.imdb_rating,
        page_url: movie.imdb_page_url,
      },
      tmdb: {
        rating: movie.tmdb_rating,
        page_url: movie.tmdb_page_url,
        backdrop_url: movie.backdrop_url,
        backdrop_url_hd: movie.backdrop_url_hd,
      },
      rt: {
        rating: movie.rt_tomatometer,
        tomatometer: movie.rt_tomatometer,
        popcornmeter: movie.rt_popcornmeter,
        page_url: movie.rt_page_url,
      },
    };

    // Add to ranklist storage
    const added = MovieStorage.add(ranklistMovie);

    if (added) {
      // If ranklist is visible, render the new card
      if (typeof MovieRenderer !== "undefined") {
        MovieRenderer.renderAll();
      }

      // Show the ranklist modal if we're on watchlist view
      if (typeof RanklistModal !== "undefined" && RanklistModal.isMinimized) {
        RanklistModal.flash();
      }

      showToast(`Added "${movie.title}" to ranklist`, "success");
    } else {
      showToast("Movie already in ranklist", "warning");
    }
  },

  /**
   * Refresh genres list (after adding new movies)
   */
  async refreshGenres() {
    this.genres = await WatchlistStorage.getGenres();
    this.renderFilters();
    this.setupFilterListeners();
  },
};
