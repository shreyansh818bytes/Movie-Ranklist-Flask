// API Handler - Two-phase lazy loading with per-platform ratings

// Keyboard shortcut tooltip management
let shortcutTooltip = null;
let tooltipShowTimeout = null;
let currentFocusedInput = null;

function createShortcutTooltip() {
  if (shortcutTooltip) return shortcutTooltip;

  shortcutTooltip = document.createElement('div');
  shortcutTooltip.className = 'shortcut-tooltip';
  shortcutTooltip.innerHTML = '<kbd>Ctrl</kbd> + <kbd>Enter</kbd> to submit';
  document.body.appendChild(shortcutTooltip);
  return shortcutTooltip;
}

function showShortcutTooltip(inputElement) {
  const tooltip = createShortcutTooltip();

  // Position tooltip near the input
  const rect = inputElement.getBoundingClientRect();
  tooltip.style.top = `${rect.bottom + window.scrollY + 8}px`;
  tooltip.style.left = `${rect.left + window.scrollX}px`;

  // Show tooltip
  tooltip.classList.add('tooltip-visible');
}

function hideShortcutTooltip() {
  if (shortcutTooltip) {
    shortcutTooltip.classList.remove('tooltip-visible');
  }
  clearTimeout(tooltipShowTimeout);
  tooltipShowTimeout = null;
  currentFocusedInput = null;
}

// Check if device is touch-capable (mobile/tablet)
function isTouchDevice() {
  return (('ontouchstart' in window) ||
    (navigator.maxTouchPoints > 0) ||
    (navigator.msMaxTouchPoints > 0));
}

// Scroll input into view when keyboard opens on mobile
function scrollInputIntoView(inputElement) {
  if (!isTouchDevice()) return;

  // Wait for keyboard to appear
  setTimeout(() => {
    // Scroll the input into view with some padding
    inputElement.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    });
  }, 300);
}

// Setup keyboard shortcuts and tooltip for search inputs
function setupSearchShortcuts() {
  const singleInput = document.getElementById('single_text_input');
  const multiInput = document.getElementById('text_area_input');

  const handleKeydown = (e) => {
    // Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      hideShortcutTooltip();
      postSearchRequest(singleInput, multiInput);
    }
  };

  const handleFocus = (e) => {
    // Scroll input into view on mobile when keyboard opens
    scrollInputIntoView(e.target);

    // Schedule tooltip to show after 5 seconds of focus
    currentFocusedInput = e.target;
    clearTimeout(tooltipShowTimeout);
    tooltipShowTimeout = setTimeout(() => {
      if (currentFocusedInput && currentFocusedInput.value.length > 0) {
        showShortcutTooltip(currentFocusedInput);
      }
    }, 5000);
  };

  const handleInput = (e) => {
    // Hide tooltip if field becomes empty
    if (e.target.value.length === 0) {
      if (shortcutTooltip) {
        shortcutTooltip.classList.remove('tooltip-visible');
      }
    }
  };

  const handleBlur = () => {
    hideShortcutTooltip();
  };

  if (singleInput) {
    singleInput.addEventListener('keydown', handleKeydown);
    singleInput.addEventListener('focus', handleFocus);
    singleInput.addEventListener('input', handleInput);
    singleInput.addEventListener('blur', handleBlur);
  }

  if (multiInput) {
    multiInput.addEventListener('keydown', handleKeydown);
    multiInput.addEventListener('focus', handleFocus);
    multiInput.addEventListener('input', handleInput);
    multiInput.addEventListener('blur', handleBlur);
  }
}

// Initialize shortcuts when DOM is ready
document.addEventListener('DOMContentLoaded', setupSearchShortcuts);

function showLoadingButton(buttonId) {
  const button = document.getElementById(buttonId);
  if (button) {
    button.setAttribute("disabled", true);
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';
  }
}

function resetButton(buttonId) {
  const button = document.getElementById(buttonId);
  if (button) {
    button.removeAttribute("disabled");
    button.innerHTML = button.dataset.originalText || 'Add';
  }
}

function parseSearchInput(singleInput, multiInput) {
  const queries = [];
  const seen = new Set();

  // Add single input
  if (singleInput && singleInput.trim()) {
    const q = singleInput.trim();
    if (!seen.has(q.toLowerCase())) {
      queries.push({ query: q });
      seen.add(q.toLowerCase());
    }
  }

  // Add multi-line input
  if (multiInput) {
    const lines = multiInput.split("\n");
    for (const line of lines) {
      const q = line.trim();
      if (q && !seen.has(q.toLowerCase())) {
        queries.push({ query: q });
        seen.add(q.toLowerCase());
      }
    }
  }

  return queries;
}

function filterDuplicates(queries) {
  const existingMovies = MovieStorage.getAll();
  const existingQueries = new Set(existingMovies.map((m) => m.query.toLowerCase()));

  return queries.filter((q) => !existingQueries.has(q.query.toLowerCase()));
}

// Fetch rating from a specific platform
async function fetchPlatformRating(movieId, platform, title, year) {
  let url = `/api/movies/${encodeURIComponent(movieId)}/rating/${platform}`;

  if (platform === 'tmdb' || platform === 'rt') {
    const params = new URLSearchParams({ title });
    if (year) params.append('year', year);
    url += `?${params.toString()}`;
  }

  try {
    const response = await fetch(url);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching ${platform} rating for ${movieId}:`, error);
    return { rating: null, page_url: '' };
  }
}

// Fetch all ratings for a movie and update UI progressively
async function fetchAllRatingsForMovie(movie) {
  const movieId = movie.id;
  const title = movie.title;
  const year = movie.year;

  // Track pending ratings to know when all are done
  let pendingCount = 3;
  const checkAndReorder = () => {
    pendingCount--;
    if (pendingCount === 0) {
      // All ratings loaded, finalize the card
      MovieRenderer.finalizeShellCard(movieId);
      MovieRenderer.reorderWithAnimation();
    }
  };

  // Fetch IMDb rating
  fetchPlatformRating(movieId, 'imdb', title, year).then(data => {
    MovieRenderer.updateRatingPill(movieId, 'imdb', data);

    // Update storage
    const result = MovieStorage.updateMovie(movieId, {
      imdb: {
        rating: data.rating,
        page_url: data.page_url,
      }
    });

    if (result) {
      MovieRenderer.updateAverageScore(movieId, result.movie.average_score);
    }

    checkAndReorder();
  });

  // Fetch TMDb rating
  fetchPlatformRating(movieId, 'tmdb', title, year).then(data => {
    MovieRenderer.updateRatingPill(movieId, 'tmdb', data);

    // Update storage with backdrop info too
    const result = MovieStorage.updateMovie(movieId, {
      tmdb: {
        rating: data.rating,
        page_url: data.page_url,
        backdrop_url: data.backdrop_url,
        backdrop_url_hd: data.backdrop_url_hd,
      },
      backdrop_url: data.backdrop_url || undefined,
      backdrop_url_hd: data.backdrop_url_hd || undefined,
    });

    if (result) {
      MovieRenderer.updateAverageScore(movieId, result.movie.average_score);

      // Update backdrop preview if available
      if (data.backdrop_url) {
        const card = document.getElementById(movieId);
        if (card) {
          const existingStyle = card.querySelector('style');
          if (existingStyle) existingStyle.remove();

          const style = document.createElement('style');
          style.textContent = `
            #${CSS.escape(movieId)}::before {
              background-image: url(${data.backdrop_url});
            }
          `;
          card.appendChild(style);
        }
      }

      // Add backdrop button if HD URL is available
      if (data.backdrop_url_hd) {
        const actionsContainer = document.getElementById(`${movieId}-actions`);
        const deleteBtn = document.getElementById(`${movieId}-dlt-btn`);
        if (actionsContainer && deleteBtn && !document.getElementById(`${movieId}-backdrop-btn`)) {
          const backdropBtn = document.createElement('button');
          backdropBtn.className = 'icon-button action-btn backdrop-button';
          backdropBtn.type = 'button';
          backdropBtn.id = `${movieId}-backdrop-btn`;
          backdropBtn.setAttribute('onclick', `openBackdrop('${movieId}')`);
          backdropBtn.setAttribute('data-tooltip', 'View HD backdrop');
          backdropBtn.innerHTML = '<i class="fa fa-image"></i>';
          actionsContainer.insertBefore(backdropBtn, deleteBtn);
        }
      }
    }

    checkAndReorder();
  });

  // Fetch RT rating
  fetchPlatformRating(movieId, 'rt', title, year).then(data => {
    MovieRenderer.updateRatingPill(movieId, 'rt', data);

    // Update storage
    const result = MovieStorage.updateMovie(movieId, {
      rt: {
        rating: data.rating,
        page_url: data.page_url,
      }
    });

    if (result) {
      MovieRenderer.updateAverageScore(movieId, result.movie.average_score);
    }

    checkAndReorder();
  });
}

async function postSearchRequest(singleInputComponent, multiInputComponent) {
  const singleValue = singleInputComponent?.value || "";
  const multiValue = multiInputComponent?.value || "";

  // Parse and filter duplicates
  let queries = parseSearchInput(singleValue, multiValue);
  queries = filterDuplicates(queries);

  if (queries.length === 0) {
    showToast("All movies are already in your list or no input provided.", "warning");
    return;
  }

  // Clear inputs immediately for better UX
  if (singleInputComponent) singleInputComponent.value = "";
  if (multiInputComponent) multiInputComponent.value = "";

  showLoadingButton("submit_btn");

  // Phase 1: Add skeleton cards immediately
  const skeletons = MovieRenderer.addSkeletons(queries);

  try {
    // Phase 2: Search for movie metadata (no ratings)
    const response = await fetch("/api/movies/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ movies: queries }),
    });

    const data = await response.json();

    if (data.movies && data.movies.length > 0) {
      let addedCount = 0;

      // Build a map of query -> skeleton for efficient lookup and removal
      const skeletonMap = new Map();
      for (const s of skeletons) {
        skeletonMap.set(s.query.toLowerCase(), s);
      }

      // Replace skeletons with shell cards (have metadata, spinners for ratings)
      data.movies.forEach((movie, index) => {
        // Find matching skeleton by query
        const queryKey = movie.query.toLowerCase();
        const matchingSkeleton = skeletonMap.get(queryKey);

        if (matchingSkeleton) {
          // Remove from map to prevent reuse
          skeletonMap.delete(queryKey);

          const skeleton = document.getElementById(matchingSkeleton.tempId);
          if (skeleton) {
            // Create shell card with spinners
            const shellCard = MovieRenderer.createShellCard(movie, '?');
            shellCard.classList.add('card-fade-in');

            // Replace skeleton with shell card
            skeleton.parentNode.replaceChild(shellCard, skeleton);

            // Initialize movie in storage with basic data (no ratings yet)
            const movieData = {
              id: movie.id,
              query: movie.query,
              title: movie.title,
              year: movie.year,
              logo_url: movie.logo_url,
              average_score: 0,
              backdrop_url: '',
              backdrop_url_hd: '',
              imdb: { rating: null, page_url: '' },
              tmdb: { rating: null, page_url: '', backdrop_url: '', backdrop_url_hd: '' },
              rt: { rating: null, page_url: '' },
            };

            MovieStorage.add(movieData);
            addedCount++;

            // Phase 3: Fire parallel requests for each platform rating
            fetchAllRatingsForMovie(movie);
          }
        }
      });

      // Remove any remaining skeletons (for queries that weren't found)
      MovieRenderer.removeAllSkeletons();
      MovieRenderer.updateCount();

      if (addedCount > 0) {
        showToast(`Added ${addedCount} movie${addedCount > 1 ? 's' : ''} to your list!`, "success");
      }
    } else {
      // Remove skeletons if no movies returned
      MovieRenderer.removeAllSkeletons();
      showToast("No movies found for your search.", "warning");
    }

    if (data.errors && data.errors.length > 0) {
      console.warn("Some movies had errors:", data.errors);
      // Note: Skeletons for failed queries are already removed by removeAllSkeletons() above

      if (data.errors.length === queries.length) {
        showToast("Could not find any of the requested movies.", "error");
      }
    }
  } catch (error) {
    console.error("Error fetching movies:", error);
    // Remove skeletons on error
    MovieRenderer.removeAllSkeletons();
    showToast("Failed to fetch movie data. Please try again.", "error");
  } finally {
    resetButton("submit_btn");
  }
}

// Refresh ratings for a single movie
async function refreshMovie(movieId) {
  const movie = MovieStorage.get(movieId);
  if (!movie) {
    showToast("Movie not found", "error");
    return;
  }

  const refreshBtn = document.getElementById(`${movieId}-refresh-btn`);
  if (refreshBtn) {
    refreshBtn.setAttribute("disabled", true);
    refreshBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
  }

  // Reset rating pills to loading state
  const ratingsContainer = document.getElementById(`${movieId}-ratings`);
  if (ratingsContainer) {
    ratingsContainer.innerHTML = `
      <div class="icon-text-pill rating-pill-loading" data-platform="imdb" id="${movieId}-imdb-pill">
        <img src="/static/assets/imdb-icon.svg" alt="IMDb" />
        <i class="fa fa-spinner fa-spin rating-spinner"></i>
      </div>
      <div class="icon-text-pill rating-pill-loading" data-platform="tmdb" id="${movieId}-tmdb-pill">
        <img src="/static/assets/tmdb-icon.svg" alt="TMDb" />
        <i class="fa fa-spinner fa-spin rating-spinner"></i>
      </div>
      <div class="icon-text-pill rating-pill-loading" data-platform="rt" id="${movieId}-rt-pill">
        <img src="/static/assets/rt-icon.svg" alt="RT" />
        <i class="fa fa-spinner fa-spin rating-spinner"></i>
      </div>
    `;
  }

  // Reset average score to loading state
  const avgScoreEl = document.getElementById(`${movieId}-avg-score`);
  if (avgScoreEl) {
    avgScoreEl.classList.add('avg-score-loading');
    avgScoreEl.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
  }

  // Track pending ratings
  let pendingCount = 3;
  const checkAndFinalize = () => {
    pendingCount--;
    if (pendingCount === 0) {
      // All ratings refreshed
      if (refreshBtn) {
        refreshBtn.removeAttribute("disabled");
        refreshBtn.innerHTML = '<i class="fa fa-refresh"></i>';
      }
      MovieRenderer.reorderWithAnimation();
      showToast("Ratings refreshed!", "success");
    }
  };

  const title = movie.title;
  const year = movie.year;

  // Fetch IMDb rating
  fetchPlatformRating(movieId, 'imdb', title, year).then(data => {
    MovieRenderer.updateRatingPill(movieId, 'imdb', data);
    const result = MovieStorage.updateMovie(movieId, {
      imdb: { rating: data.rating, page_url: data.page_url }
    });
    if (result) {
      MovieRenderer.updateAverageScore(movieId, result.movie.average_score);
    }
    checkAndFinalize();
  });

  // Fetch TMDb rating
  fetchPlatformRating(movieId, 'tmdb', title, year).then(data => {
    MovieRenderer.updateRatingPill(movieId, 'tmdb', data);
    const result = MovieStorage.updateMovie(movieId, {
      tmdb: { rating: data.rating, page_url: data.page_url, backdrop_url: data.backdrop_url, backdrop_url_hd: data.backdrop_url_hd },
      backdrop_url: data.backdrop_url || undefined,
      backdrop_url_hd: data.backdrop_url_hd || undefined,
    });
    if (result) {
      MovieRenderer.updateAverageScore(movieId, result.movie.average_score);
    }
    // Add or remove backdrop button based on HD URL availability
    const actionsContainer = document.getElementById(`${movieId}-actions`);
    const existingBackdropBtn = document.getElementById(`${movieId}-backdrop-btn`);
    const deleteBtn = document.getElementById(`${movieId}-dlt-btn`);

    if (data.backdrop_url_hd) {
      if (!existingBackdropBtn && actionsContainer && deleteBtn) {
        const backdropBtn = document.createElement('button');
        backdropBtn.className = 'icon-button action-btn backdrop-button';
        backdropBtn.type = 'button';
        backdropBtn.id = `${movieId}-backdrop-btn`;
        backdropBtn.setAttribute('onclick', `openBackdrop('${movieId}')`);
        backdropBtn.setAttribute('data-tooltip', 'View HD backdrop');
        backdropBtn.innerHTML = '<i class="fa fa-image"></i>';
        actionsContainer.insertBefore(backdropBtn, deleteBtn);
      }
    } else if (existingBackdropBtn) {
      existingBackdropBtn.remove();
    }
    checkAndFinalize();
  });

  // Fetch RT rating
  fetchPlatformRating(movieId, 'rt', title, year).then(data => {
    MovieRenderer.updateRatingPill(movieId, 'rt', data);
    const result = MovieStorage.updateMovie(movieId, {
      rt: { rating: data.rating, page_url: data.page_url }
    });
    if (result) {
      MovieRenderer.updateAverageScore(movieId, result.movie.average_score);
    }
    checkAndFinalize();
  });
}

// Simple toast notification system
function showToast(message, type = "info") {
  // Remove existing toast
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    existingToast.remove();
  }

  const toast = document.createElement('div');
  toast.className = `toast-notification toast-${type}`;

  const icons = {
    success: 'fa-check-circle',
    error: 'fa-exclamation-circle',
    warning: 'fa-exclamation-triangle',
    info: 'fa-info-circle'
  };

  toast.innerHTML = `
    <i class="fa ${icons[type] || icons.info}"></i>
    <span>${message}</span>
  `;

  document.body.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add('toast-show');
  });

  // Auto-remove after 3 seconds
  setTimeout(() => {
    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
