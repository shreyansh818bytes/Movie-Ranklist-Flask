// View Controller - Navigation between Watchlist and Ranklist views

const ViewController = {
  // Current active view: "watchlist" or "ranklist"
  currentView: "ranklist",

  // Whether user is authenticated
  isAuthenticated: false,

  // Cached watchlist data for quick checks
  watchlistMovies: [],

  /**
   * Initialize the view controller
   */
  async init() {
    // Check authentication status
    const authStatus = await this.checkAuth();
    this.isAuthenticated = authStatus.authenticated;

    // Setup tab click handlers
    this.setupTabListeners();

    // Determine initial view based on URL path and auth status
    const path = window.location.pathname;
    const urlRequestsRanklist = path === "/ranklist";

    if (urlRequestsRanklist) {
      // URL explicitly requests ranklist
      this.switchViewWithoutPush("ranklist");
    } else if (this.isAuthenticated) {
      // Logged-in users see watchlist by default
      this.switchViewWithoutPush("watchlist");
    } else {
      // Non-logged-in users see ranklist by default
      this.switchViewWithoutPush("ranklist");
    }

    // Update UI based on auth status
    this.updateAuthUI();
  },

  /**
   * Check authentication status
   */
  async checkAuth() {
    try {
      const response = await fetch("/api/auth/status");
      return await response.json();
    } catch (error) {
      console.error("Failed to check auth status:", error);
      return { authenticated: false };
    }
  },

  /**
   * Setup tab click event listeners
   */
  setupTabListeners() {
    const watchlistTab = document.getElementById("tab-watchlist");
    const ranklistTab = document.getElementById("tab-ranklist");

    if (watchlistTab) {
      watchlistTab.addEventListener("click", (e) => {
        e.preventDefault();
        if (this.isAuthenticated) {
          this.switchView("watchlist");
        } else {
          // Redirect to login
          window.location.href = "/login";
        }
      });
    }

    if (ranklistTab) {
      ranklistTab.addEventListener("click", (e) => {
        e.preventDefault();
        this.switchView("ranklist");
      });
    }
  },

  /**
   * Switch between views (internal, without pushing to history)
   * @param {string} view - "watchlist" or "ranklist"
   */
  async switchViewWithoutPush(view) {
    this.currentView = view;

    // Show/hide containers
    const watchlistContainer = document.getElementById("watchlist-container");
    const ranklistContainer = document.getElementById("ranklist-container");

    if (watchlistContainer) {
      watchlistContainer.style.display = view === "watchlist" ? "flex" : "none";
    }
    if (ranklistContainer) {
      ranklistContainer.style.display = view === "ranklist" ? "flex" : "none";
    }

    // Initialize the appropriate view
    if (view === "watchlist") {
      await WatchlistRenderer.init();

      // Show minimized ranklist modal
      if (typeof RanklistModal !== "undefined") {
        RanklistModal.show();
      }
    } else {
      // Hide ranklist modal when on ranklist view
      if (typeof RanklistModal !== "undefined") {
        RanklistModal.hide();
      }

      // Re-render ranklist to ensure it's up to date
      if (typeof MovieRenderer !== "undefined") {
        MovieRenderer.renderAll();
      }
    }

    // Update back button visibility
    this.updateBackButton();
  },

  /**
   * Switch between views (pushes to history)
   * @param {string} view - "watchlist" or "ranklist"
   */
  async switchView(view) {
    await this.switchViewWithoutPush(view);

    // Update URL path without triggering page reload
    const newPath = view === "watchlist" ? "/" : "/ranklist";
    history.pushState({ view }, "", newPath);
  },

  /**
   * Update UI based on authentication status
   */
  updateAuthUI() {
    const createWatchlistBtn = document.getElementById("create-watchlist-btn");
    const backBtn = document.getElementById("back-to-watchlist-btn");

    if (this.isAuthenticated) {
      // Hide "Create Watchlist" button for logged-in users
      if (createWatchlistBtn) {
        createWatchlistBtn.style.display = "none";
      }
    } else {
      // Show "Create Watchlist" button for non-logged-in users
      if (createWatchlistBtn) {
        createWatchlistBtn.style.display = "flex";
      }
      // Hide back button for non-logged-in users
      if (backBtn) {
        backBtn.style.display = "none";
      }
    }

    // Update back button visibility based on current view
    this.updateBackButton();
  },

  /**
   * Update back button visibility based on current view and auth status
   */
  updateBackButton() {
    const backBtn = document.getElementById("back-to-watchlist-btn");
    if (!backBtn) return;

    // Show back button only for logged-in users on ranklist view
    if (this.isAuthenticated && this.currentView === "ranklist") {
      backBtn.style.display = "flex";
    } else {
      backBtn.style.display = "none";
    }
  },

  /**
   * Show a prompt to save ranklist to watchlist
   */
  showWatchlistPrompt() {
    const count = MovieStorage.count();
    if (count > 0) {
      // User has movies in ranklist but no watchlist - show prompt
      const prompt = document.createElement("div");
      prompt.className = "watchlist-prompt";
      prompt.innerHTML = `
        <i class="fa fa-bookmark"></i>
        <span>You have ${count} movie${count > 1 ? "s" : ""} in your ranklist. Save them to your watchlist?</span>
        <button class="btn btn-sm btn-accent" onclick="ViewController.saveRanklistToWatchlist()">
          <i class="fa fa-plus me-1"></i>Save All
        </button>
        <button class="btn btn-sm btn-outline-light" onclick="this.parentElement.remove()">
          <i class="fa fa-times"></i>
        </button>
      `;

      const container = document.getElementById("output-container") || document.getElementById("ranklist-container");
      if (container) {
        container.insertBefore(prompt, container.firstChild);
      }
    }
  },

  /**
   * Save all ranklist movies to watchlist
   */
  async saveRanklistToWatchlist() {
    if (!this.isAuthenticated) {
      showToast("Please log in to save to watchlist", "warning");
      return;
    }

    const movies = MovieStorage.getAll();
    if (movies.length === 0) {
      showToast("No movies in ranklist to save", "warning");
      return;
    }

    showToast("Saving movies to watchlist...", "info");

    const result = await WatchlistStorage.addBulk(movies);

    if (result.success) {
      const addedCount = result.added_count || 0;
      const skippedCount = result.skipped_count || 0;

      if (addedCount > 0) {
        showToast(`Added ${addedCount} movie${addedCount > 1 ? "s" : ""} to watchlist`, "success");
      }
      if (skippedCount > 0) {
        showToast(`${skippedCount} movie${skippedCount > 1 ? "s" : ""} already in watchlist`, "info");
      }

      // Remove the prompt
      const prompt = document.querySelector(".watchlist-prompt");
      if (prompt) {
        prompt.remove();
      }

      // Refresh watchlist genres
      if (typeof WatchlistRenderer !== "undefined") {
        WatchlistRenderer.refreshGenres();
      }
    } else {
      showToast(result.error || "Failed to save to watchlist", "error");
    }
  },

  /**
   * Check if user is authenticated (for external use)
   */
  getIsAuthenticated() {
    return this.isAuthenticated;
  },

  /**
   * Refresh authentication status
   */
  async refreshAuth() {
    const authStatus = await this.checkAuth();
    this.isAuthenticated = authStatus.authenticated;
    this.updateAuthUI();
    return this.isAuthenticated;
  },
};

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  ViewController.init();
});

// Handle browser back/forward navigation
window.addEventListener("popstate", (event) => {
  if (event.state && event.state.view) {
    ViewController.switchViewWithoutPush(event.state.view);
  } else {
    // Determine view from URL path
    const path = window.location.pathname;
    const view = path === "/ranklist" ? "ranklist" : "watchlist";
    ViewController.switchViewWithoutPush(view);
  }
});
