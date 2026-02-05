// Ranklist Modal - Minimized floating modal for ranklist when on watchlist view

const RanklistModal = {
  isMinimized: true,
  isVisible: false,
  isDragging: false,
  dragOffset: { x: 0, y: 0 },

  /**
   * Get the modal element
   */
  getModal() {
    return document.getElementById("ranklist-modal");
  },

  /**
   * Initialize drag functionality
   */
  initDrag() {
    const modal = this.getModal();
    if (!modal) return;

    const header = modal.querySelector(".modal-header");
    if (!header) return;

    // Prevent re-initializing
    if (header.dataset.dragInitialized) return;
    header.dataset.dragInitialized = "true";

    // Mouse events
    header.addEventListener("mousedown", (e) => this.startDrag(e));
    document.addEventListener("mousemove", (e) => this.drag(e));
    document.addEventListener("mouseup", () => this.endDrag());

    // Touch events for mobile
    header.addEventListener("touchstart", (e) => this.startDrag(e), { passive: false });
    document.addEventListener("touchmove", (e) => this.drag(e), { passive: false });
    document.addEventListener("touchend", () => this.endDrag());
  },

  /**
   * Start dragging the modal
   * @param {MouseEvent|TouchEvent} e
   */
  startDrag(e) {
    // Don't start drag if clicking on buttons
    if (e.target.closest("button")) return;

    const modal = this.getModal();
    if (!modal) return;

    this.isDragging = true;
    modal.classList.add("dragging");

    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const rect = modal.getBoundingClientRect();

    this.dragOffset = {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };

    e.preventDefault();
  },

  /**
   * Handle drag movement
   * @param {MouseEvent|TouchEvent} e
   */
  drag(e) {
    if (!this.isDragging) return;

    const modal = this.getModal();
    if (!modal) return;

    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;

    let newX = clientX - this.dragOffset.x;
    let newY = clientY - this.dragOffset.y;

    // Constrain to viewport
    const rect = modal.getBoundingClientRect();
    const maxX = window.innerWidth - rect.width;
    const maxY = window.innerHeight - rect.height;

    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));

    // Use left/top instead of right/bottom for positioning
    modal.style.left = `${newX}px`;
    modal.style.top = `${newY}px`;
    modal.style.right = "auto";
    modal.style.bottom = "auto";

    e.preventDefault();
  },

  /**
   * End dragging
   */
  endDrag() {
    if (!this.isDragging) return;

    this.isDragging = false;
    const modal = this.getModal();
    if (modal) {
      modal.classList.remove("dragging");
    }
  },

  /**
   * Reset modal position to default
   */
  resetPosition() {
    const modal = this.getModal();
    if (modal) {
      modal.style.left = "auto";
      modal.style.top = "auto";
      modal.style.right = "1rem";
      modal.style.bottom = "1rem";
    }
  },

  /**
   * Show the modal
   */
  show() {
    const modal = this.getModal();
    if (modal) {
      modal.style.display = "flex";
      this.isVisible = true;
      this.updateContent();
      this.initDrag();
    }
  },

  /**
   * Hide the modal
   */
  hide() {
    const modal = this.getModal();
    if (modal) {
      modal.style.display = "none";
      this.isVisible = false;
    }
  },

  /**
   * Toggle between minimized and expanded states
   */
  toggle() {
    this.isMinimized = !this.isMinimized;
    const modal = this.getModal();
    if (modal) {
      modal.classList.toggle("expanded", !this.isMinimized);
      this.updateContent();
    }
  },

  /**
   * Flash the modal to indicate a new item was added
   */
  flash() {
    const modal = this.getModal();
    if (modal) {
      modal.classList.add("modal-flash");
      setTimeout(() => {
        modal.classList.remove("modal-flash");
      }, 500);
      this.updateContent();
    }
  },

  /**
   * Update the modal content based on current ranklist
   */
  updateContent() {
    const modal = this.getModal();
    if (!modal) return;

    const movies = MovieStorage.getAll();
    const count = movies.length;

    const header = modal.querySelector(".modal-header");
    const content = modal.querySelector(".modal-content");

    if (header) {
      header.innerHTML = `
        <div class="modal-title" onclick="RanklistModal.goToRanklist()" data-tooltip="Open ranklist">
          <i class="fa fa-list-ol me-2"></i>
          <span>Ranklist</span>
          <span class="modal-count">${count}</span>
        </div>
        <div class="modal-actions">
          ${count > 0 ? `
            <button class="modal-action-btn" onclick="RanklistModal.addAllToWatchlist()" title="Add all to watchlist">
              <i class="fa fa-bookmark"></i>
            </button>
            <button class="modal-action-btn" onclick="RanklistModal.clearRanklist()" title="Clear ranklist">
              <i class="fa fa-trash"></i>
            </button>
          ` : ""}
          <button class="modal-toggle-btn" onclick="RanklistModal.toggle()">
            <i class="fa fa-chevron-${this.isMinimized ? "up" : "down"}"></i>
          </button>
        </div>
      `;
    }

    if (content) {
      if (this.isMinimized) {
        content.innerHTML = "";
      } else {
        if (count === 0) {
          content.innerHTML = `
            <div class="modal-empty">
              <i class="fa fa-film"></i>
              <p>No movies in ranklist</p>
              <p class="text-muted">Add movies to compare them</p>
            </div>
          `;
        } else {
          content.innerHTML = movies
            .slice(0, 10) // Show max 10 in modal
            .map((movie, index) => this.createMiniCard(movie, index + 1))
            .join("");

          if (count > 10) {
            content.innerHTML += `
              <div class="modal-more">
                <button class="btn btn-sm btn-outline-light" onclick="ViewController.switchView('ranklist')">
                  View all ${count} movies
                </button>
              </div>
            `;
          }
        }
      }
    }
  },

  /**
   * Create a mini card for the modal list
   * @param {Object} movie
   * @param {number} rank
   */
  createMiniCard(movie, rank) {
    const score = movie.average_score ? movie.average_score.toFixed(1) : "--";
    const imdbUrl = movie.imdb?.page_url || `https://www.imdb.com/title/${movie.id}/`;

    return `
      <div class="modal-movie-card" data-id="${movie.id}" onclick="RanklistModal.openMoviePage('${imdbUrl}', event)" data-tooltip="Open IMDb">
        <span class="modal-movie-rank">${rank}</span>
        <img src="${movie.logo_url || "/static/assets/not-found-icon.svg"}" alt="${movie.title}" class="modal-movie-poster" />
        <div class="modal-movie-info">
          <span class="modal-movie-title">${movie.title}</span>
          <span class="modal-movie-year">${movie.year || ""}</span>
        </div>
        <span class="modal-movie-score">${score}</span>
        <button class="modal-movie-remove" onclick="RanklistModal.removeFromRanklist('${movie.id}')" data-tooltip="Remove">
          <i class="fa fa-times"></i>
        </button>
      </div>
    `;
  },

  /**
   * Open the movie's IMDB page
   * @param {string} url
   * @param {Event} event
   */
  openMoviePage(url, event) {
    // Don't navigate if clicking the remove button
    if (event.target.closest('.modal-movie-remove')) {
      return;
    }
    window.open(url, '_blank', 'noopener,noreferrer');
  },

  /**
   * Navigate to the ranklist page
   */
  goToRanklist() {
    if (typeof ViewController !== "undefined") {
      ViewController.switchView("ranklist");
    }
  },

  /**
   * Remove a movie from the ranklist
   * @param {string} movieId
   */
  removeFromRanklist(movieId) {
    const movie = MovieStorage.get(movieId);
    if (MovieStorage.remove(movieId)) {
      this.updateContent();
      showToast(`Removed "${movie?.title || "movie"}" from ranklist`, "success");
    }
  },

  /**
   * Clear all movies from the ranklist
   */
  clearRanklist() {
    const count = MovieStorage.count();
    if (count === 0) return;

    if (confirm(`Remove all ${count} movies from ranklist?`)) {
      // Clear localStorage
      MovieStorage.saveAll([]);
      this.updateContent();

      // Also update the main ranklist view if visible
      if (typeof MovieRenderer !== "undefined") {
        MovieRenderer.renderAll();
      }

      showToast("Ranklist cleared", "success");
    }
  },

  /**
   * Add all ranklist movies to watchlist
   */
  async addAllToWatchlist() {
    if (!ViewController.getIsAuthenticated()) {
      showToast("Please log in to save to watchlist", "warning");
      return;
    }

    const movies = MovieStorage.getAll();
    if (movies.length === 0) {
      showToast("No movies in ranklist", "warning");
      return;
    }

    showToast("Adding to watchlist...", "info");

    const result = await WatchlistStorage.addBulk(movies);

    if (result.success) {
      const addedCount = result.added_count || 0;
      const skippedCount = result.skipped_count || 0;

      if (addedCount > 0) {
        showToast(`Added ${addedCount} movie${addedCount > 1 ? "s" : ""} to watchlist`, "success");
      }
      if (skippedCount > 0 && addedCount === 0) {
        showToast("All movies already in watchlist", "info");
      }

      // Refresh watchlist if on watchlist view
      if (ViewController.currentView === "watchlist") {
        WatchlistRenderer.loadAndRender();
        WatchlistRenderer.refreshGenres();
      }
    } else {
      showToast(result.error || "Failed to add to watchlist", "error");
    }
  },
};
