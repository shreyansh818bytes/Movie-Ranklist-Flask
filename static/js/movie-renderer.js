// Movie Renderer - Dynamic DOM rendering with skeleton loading
const MovieRenderer = {
  getContainer() {
    return document.querySelector(".movie-list-container");
  },

  updateCount() {
    const count = MovieStorage.count();
    const skeletonCount = document.querySelectorAll('.movie-skeleton').length;
    const shellCount = document.querySelectorAll('.movie-shell').length;
    const total = count + skeletonCount + shellCount;
    document.getElementById("movie-total").textContent = `${total} Movie${total !== 1 ? 's' : ''} Listed`;
  },

  // Create a skeleton placeholder card (initial loading state)
  createSkeletonCard(query, tempId) {
    const container = document.createElement("div");
    container.className = "movie-container movie-skeleton";
    container.id = tempId;
    container.setAttribute('data-query', query);

    container.innerHTML = `
      <!-- Skeleton Thumbnail -->
      <div class="logo-box-container skeleton-pulse">
        <div class="skeleton-box" style="width: 100%; height: 100%;"></div>
      </div>

      <!-- Skeleton Info -->
      <div class="movie-info-container">
        <div class="title-year-container">
          <span class="skeleton-text skeleton-pulse" style="width: 70%;">&nbsp;</span>
          <h3 class="skeleton-text skeleton-pulse" style="width: 40%;">&nbsp;</h3>
        </div>

        <!-- Skeleton Rating Pills -->
        <div class="ratings-container">
          <div class="skeleton-pill skeleton-pulse"></div>
          <div class="skeleton-pill skeleton-pulse"></div>
        </div>
      </div>

      <!-- Skeleton Score -->
      <div class="avg-score skeleton-score skeleton-pulse">
        <span>--</span>
      </div>
    `;

    return container;
  },

  // Create a shell card with movie metadata and loading spinners for ratings
  createShellCard(movie, rank) {
    const container = document.createElement("div");
    container.className = "movie-container movie-shell";
    container.id = movie.id;
    container.setAttribute('data-title', movie.title);
    container.setAttribute('data-year', movie.year || '');

    container.innerHTML = `
      <!-- Movie Thumbnail -->
      <div class="logo-box-container">
        <img src="${movie.logo_url || 'static/assets/not-found-icon.svg'}" alt="${movie.title}" class="logo-box" loading="lazy" />
        <!-- Movie Rank Indicator -->
        <span class="movie-rank-indicator">${rank}</span>
        <!-- Poster link button -->
        <a class="icon-button link-button-over-image" href="${movie.logo_url || '#'}" target="_blank" title="View poster">
          <img class="filter-neutral" style="width: 12px; height: 12px;" src="/static/assets/link-square.svg" alt="Link" />
        </a>
      </div>

      <!-- Movie Info -->
      <div class="movie-info-container">
        <div class="title-year-container">
          <span title="${movie.title}">${movie.title}</span>
          <h3>${movie.year || "Unknown year"}</h3>
        </div>

        <!-- Rating Pills with Spinners -->
        <div class="ratings-container" id="${movie.id}-ratings">
          <div class="icon-text-pill rating-pill-loading" data-platform="imdb" id="${movie.id}-imdb-pill">
            <img src="/static/assets/imdb-icon.svg" alt="IMDb" />
            <i class="fa fa-spinner fa-spin rating-spinner"></i>
          </div>
          <div class="icon-text-pill rating-pill-loading" data-platform="tmdb" id="${movie.id}-tmdb-pill">
            <img src="/static/assets/tmdb-icon.svg" alt="TMDb" />
            <i class="fa fa-spinner fa-spin rating-spinner"></i>
          </div>
          <div class="icon-text-pill rating-pill-loading" data-platform="rt" id="${movie.id}-rt-pill">
            <img src="/static/assets/rt-icon.svg" alt="RT" />
            <i class="fa fa-spinner fa-spin rating-spinner"></i>
          </div>
        </div>
      </div>

      <!-- Average Score (loading state, top-right) -->
      <div class="avg-score avg-score-loading" id="${movie.id}-avg-score">
        <i class="fa fa-spinner fa-spin"></i>
      </div>

      <!-- Action Buttons (visible on hover) -->
      <div class="card-actions" id="${movie.id}-actions">
        <!-- Refresh Button -->
        <button
          class="icon-button action-btn refresh-button"
          type="button"
          id="${movie.id}-refresh-btn"
          onclick="refreshMovie('${movie.id}')"
          data-tooltip="Refresh ratings"
          disabled
        >
          <i class="fa fa-refresh"></i>
        </button>

        <!-- Backdrop button will be added dynamically if HD URL is available -->

        <!-- Delete Button -->
        <button
          class="icon-button action-btn delete-button"
          type="button"
          id="${movie.id}-dlt-btn"
          onclick="deleteMovie('${movie.id}')"
          data-tooltip="Remove from list"
        >
          <i class="fa fa-trash"></i>
        </button>
      </div>
    `;

    return container;
  },

  // Update a single rating pill when data arrives
  updateRatingPill(movieId, platform, data) {
    const pill = document.getElementById(`${movieId}-${platform}-pill`);
    if (!pill) return;

    if (data.rating && data.rating > 0 && data.page_url) {
      // Convert to anchor element for the link
      const wrapper = document.createElement('a');
      wrapper.className = 'icon-text-pill rating-pill-loaded';
      wrapper.href = data.page_url;
      wrapper.target = '_blank';
      wrapper.rel = 'noopener noreferrer';
      wrapper.title = `View on ${platform.toUpperCase()}`;
      wrapper.id = `${movieId}-${platform}-pill`;
      wrapper.setAttribute('data-platform', platform);

      const iconSrc = platform === 'imdb' ? '/static/assets/imdb-icon.svg' :
                      platform === 'tmdb' ? '/static/assets/tmdb-icon.svg' :
                      '/static/assets/rt-icon.svg';

      wrapper.innerHTML = `
        <img src="${iconSrc}" alt="${platform.toUpperCase()}" />
        <p>${data.rating}</p>
        <i class="fa fa-external-link link-icon"></i>
      `;

      pill.parentNode.replaceChild(wrapper, pill);
    } else {
      // No rating available or no URL - remove the pill entirely
      pill.remove();
    }
  },

  // Update average score with animation
  updateAverageScore(movieId, score) {
    const scoreEl = document.getElementById(`${movieId}-avg-score`);
    if (!scoreEl) return;

    scoreEl.classList.remove('avg-score-loading');
    scoreEl.classList.add('avg-score-updating');

    if (score && score > 0) {
      scoreEl.innerHTML = score.toFixed(1);
    } else {
      scoreEl.innerHTML = '--';
    }

    // Remove animation class after animation completes
    setTimeout(() => {
      scoreEl.classList.remove('avg-score-updating');
    }, 400);
  },

  // FLIP animation for reordering cards
  reorderWithAnimation() {
    const container = this.getContainer();
    const cards = Array.from(container.querySelectorAll('.movie-container:not(.movie-skeleton)'));

    if (cards.length === 0) return;

    // Capture initial positions (First)
    const firstPositions = new Map();
    cards.forEach(card => {
      const rect = card.getBoundingClientRect();
      firstPositions.set(card.id, { top: rect.top, left: rect.left });
    });

    // Get sorted order from storage
    const sortedMovies = MovieStorage.getAll();
    const sortedIds = sortedMovies.map(m => m.id);

    // Check if order actually changed
    const currentIds = cards.map(c => c.id);
    const orderChanged = sortedIds.some((id, i) => currentIds[i] !== id);

    if (!orderChanged) {
      // Just update rank indicators without animation
      cards.forEach(card => {
        const newIndex = sortedIds.indexOf(card.id);
        if (newIndex !== -1) {
          const rankIndicator = card.querySelector('.movie-rank-indicator');
          if (rankIndicator) {
            rankIndicator.textContent = newIndex + 1;
          }
        }
      });
      return;
    }

    // Reorder DOM elements (perform the layout change)
    sortedIds.forEach(id => {
      const card = document.getElementById(id);
      if (card) {
        container.appendChild(card);
      }
    });

    // Force browser to calculate new layout
    container.offsetHeight;

    // Animate each card from old position to new position
    cards.forEach(card => {
      const first = firstPositions.get(card.id);
      if (!first) return;

      const last = card.getBoundingClientRect();
      const deltaY = first.top - last.top;
      const deltaX = first.left - last.left;

      // Update rank indicator
      const newIndex = sortedIds.indexOf(card.id);
      if (newIndex !== -1) {
        const rankIndicator = card.querySelector('.movie-rank-indicator');
        if (rankIndicator) {
          rankIndicator.textContent = newIndex + 1;
        }
      }

      if (Math.abs(deltaY) > 1 || Math.abs(deltaX) > 1) {
        // Invert: apply transform to put element back at old position
        card.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
        card.style.transition = 'none';
        card.classList.add('card-moved');

        // Force reflow for this specific card
        card.offsetHeight;

        // Play: animate to new position
        requestAnimationFrame(() => {
          card.style.transition = 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
          card.style.transform = 'translate(0, 0)';

          // Cleanup after animation
          card.addEventListener('transitionend', function handler() {
            card.style.transition = '';
            card.style.transform = '';
            card.classList.remove('card-moved');
            card.removeEventListener('transitionend', handler);
          }, { once: true });
        });
      }
    });
  },

  // Finalize a shell card (convert to regular movie card after all ratings loaded)
  finalizeShellCard(movieId) {
    const shell = document.getElementById(movieId);
    if (shell) {
      shell.classList.remove('movie-shell');
      shell.classList.add('card-fade-in');

      // Enable the refresh button
      const refreshBtn = document.getElementById(`${movieId}-refresh-btn`);
      if (refreshBtn) {
        refreshBtn.removeAttribute('disabled');
      }
      // Note: Backdrop button is added dynamically by api-handler when HD URL is available
    }
  },

  // Add skeleton cards for queries being fetched
  addSkeletons(queries) {
    const container = this.getContainer();
    const skeletons = [];

    queries.forEach((q, index) => {
      const query = q.query || q;
      const tempId = `skeleton-${Date.now()}-${index}`;
      const skeleton = this.createSkeletonCard(query, tempId);

      // Insert at the beginning (top of list)
      container.insertBefore(skeleton, container.firstChild);
      skeletons.push({ tempId, query });
    });

    this.updateCount();
    return skeletons;
  },

  // Remove a skeleton by ID
  removeSkeleton(tempId) {
    const skeleton = document.getElementById(tempId);
    if (skeleton) {
      skeleton.remove();
    }
  },

  // Remove all skeletons
  removeAllSkeletons() {
    document.querySelectorAll('.movie-skeleton').forEach(el => el.remove());
    this.updateCount();
  },

  createMovieCard(movie, rank) {
    const container = document.createElement("div");
    container.className = "movie-container";
    container.id = movie.id;

    // Set backdrop image for hover effect
    if (movie.backdrop_url) {
      container.setAttribute('data-backdrop', movie.backdrop_url);
    }

    // Build rating pills HTML with external link icons
    let ratingPills = "";
    if (movie.imdb && movie.imdb.rating && movie.imdb.page_url) {
      ratingPills += `
        <a href="${movie.imdb.page_url}" target="_blank" rel="noopener noreferrer" class="icon-text-pill" title="View on IMDb">
          <img src="/static/assets/imdb-icon.svg" alt="IMDb" />
          <p>${movie.imdb.rating}</p>
          <i class="fa fa-external-link link-icon"></i>
        </a>`;
    }
    if (movie.tmdb && movie.tmdb.rating && movie.tmdb.page_url) {
      ratingPills += `
        <a href="${movie.tmdb.page_url}" target="_blank" rel="noopener noreferrer" class="icon-text-pill" title="View on TMDb">
          <img src="/static/assets/tmdb-icon.svg" alt="TMDb" />
          <p>${movie.tmdb.rating}</p>
          <i class="fa fa-external-link link-icon"></i>
        </a>`;
    }
    if (movie.rt && movie.rt.rating && movie.rt.page_url) {
      ratingPills += `
        <a href="${movie.rt.page_url}" target="_blank" rel="noopener noreferrer" class="icon-text-pill" title="View on Rotten Tomatoes">
          <img src="/static/assets/rt-icon.svg" alt="RT" />
          <p>${movie.rt.rating}</p>
          <i class="fa fa-external-link link-icon"></i>
        </a>`;
    }

    container.innerHTML = `
      <!-- Movie Thumbnail -->
      <div class="logo-box-container">
        <img src="${movie.logo_url}" alt="${movie.title}" class="logo-box" loading="lazy" />
        <!-- Movie Rank Indicator -->
        <span class="movie-rank-indicator">${rank}</span>
        <!-- Poster link button -->
        <a class="icon-button link-button-over-image" href="${movie.logo_url}" target="_blank" title="View poster">
          <img class="filter-neutral" style="width: 12px; height: 12px;" src="/static/assets/link-square.svg" alt="Link" />
        </a>
      </div>

      <!-- Movie Info -->
      <div class="movie-info-container">
        <div class="title-year-container">
          <span title="${movie.title}">${movie.title}</span>
          <h3>${movie.year || "Unknown year"}</h3>
        </div>

        <!-- Rating Pills -->
        <div class="ratings-container" id="${movie.id}-ratings">
          ${ratingPills || '<span class="text-muted" style="font-size: 0.75rem;">No ratings available</span>'}
        </div>
      </div>

      <!-- Average Score (top-right) -->
      <div class="avg-score" id="${movie.id}-avg-score" title="Average rating">
        ${movie.average_score ? movie.average_score.toFixed(1) : "--"}
      </div>

      <!-- Action Buttons (visible on hover) -->
      <div class="card-actions" id="${movie.id}-actions">
        <!-- Refresh Button -->
        <button
          class="icon-button action-btn refresh-button"
          type="button"
          id="${movie.id}-refresh-btn"
          onclick="refreshMovie('${movie.id}')"
          data-tooltip="Refresh ratings"
        >
          <i class="fa fa-refresh"></i>
        </button>

        <!-- Backdrop Redirect Button (only visible if HD backdrop available) -->
        ${movie.backdrop_url_hd ? `
        <button
          class="icon-button action-btn backdrop-button"
          type="button"
          id="${movie.id}-backdrop-btn"
          onclick="openBackdrop('${movie.id}')"
          data-tooltip="View HD backdrop"
        >
          <i class="fa fa-image"></i>
        </button>` : ''}

        <!-- Delete Button -->
        <button
          class="icon-button action-btn delete-button"
          type="button"
          id="${movie.id}-dlt-btn"
          onclick="deleteMovie('${movie.id}')"
          data-tooltip="Remove from list"
        >
          <i class="fa fa-trash"></i>
        </button>
      </div>
    `;

    // Apply backdrop as inline style for the ::before pseudo-element
    if (movie.backdrop_url) {
      const style = document.createElement('style');
      style.textContent = `
        #${CSS.escape(movie.id)}::before {
          background-image: url(${movie.backdrop_url});
        }
      `;
      container.appendChild(style);
    }

    return container;
  },

  renderAll() {
    const container = this.getContainer();
    container.innerHTML = "";

    const movies = MovieStorage.getAll();
    movies.forEach((movie, index) => {
      const card = this.createMovieCard(movie, index + 1);
      container.appendChild(card);
    });

    this.updateCount();
  },

  removeMovie(movieId) {
    const removed = MovieStorage.remove(movieId);
    if (removed) {
      const card = document.getElementById(movieId);
      if (card) {
        card.classList.add('card-fade-out');
        setTimeout(() => {
          card.remove();
          this.renderAll();
        }, 200);
      } else {
        this.renderAll();
      }
    }
    return removed;
  },
};

// Global delete function called from onclick
function deleteMovie(movieId) {
  const button = document.getElementById(movieId + "-dlt-btn");
  if (button) {
    button.setAttribute("disabled", true);
    button.innerHTML = '<i class="fa fa-spinner fa-spin" style="color: #f59e0b;"></i>';
  }
  MovieRenderer.removeMovie(movieId);
}

// Global backdrop redirect function (uses HD URL)
function openBackdrop(movieId) {
  const movie = MovieStorage.get(movieId);
  if (movie && movie.backdrop_url_hd) {
    window.open(movie.backdrop_url_hd, '_blank', 'noopener,noreferrer');
  }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  MovieRenderer.renderAll();
  setupActionButtonTooltips();
});

// Action button tooltip management (fixed positioning to escape overflow)
let actionTooltip = null;

function getActionTooltip() {
  if (!actionTooltip) {
    actionTooltip = document.createElement('div');
    actionTooltip.className = 'action-btn-tooltip';
    document.body.appendChild(actionTooltip);
  }
  return actionTooltip;
}

function showActionTooltip(button) {
  const tooltip = getActionTooltip();
  const text = button.getAttribute('data-tooltip');
  if (!text) return;

  tooltip.textContent = text;

  // Position tooltip above the button
  const rect = button.getBoundingClientRect();
  tooltip.style.left = `${rect.left + rect.width / 2}px`;
  tooltip.style.top = `${rect.top - 8}px`;
  tooltip.style.transform = 'translate(-50%, -100%)';

  tooltip.classList.add('visible');
}

function hideActionTooltip() {
  if (actionTooltip) {
    actionTooltip.classList.remove('visible');
  }
}

function setupActionButtonTooltips() {
  // Use event delegation on the movie list container
  const container = document.querySelector('.movie-list-container');
  if (!container) return;

  container.addEventListener('mouseenter', (e) => {
    const btn = e.target.closest('.action-btn[data-tooltip]');
    if (btn) {
      showActionTooltip(btn);
    }
  }, true);

  container.addEventListener('mouseleave', (e) => {
    const btn = e.target.closest('.action-btn[data-tooltip]');
    if (btn) {
      hideActionTooltip();
    }
  }, true);
}
