// Movie Storage - localStorage CRUD operations
const STORAGE_KEY = "movie_ranklist";

const MovieStorage = {
  getAll() {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return [];
    try {
      return JSON.parse(data);
    } catch {
      return [];
    }
  },

  saveAll(movies) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(movies));
  },

  get(movieId) {
    const movies = this.getAll();
    return movies.find((m) => m.id === movieId) || null;
  },

  add(movie) {
    const movies = this.getAll();
    // Check for duplicates by ID
    if (movies.some((m) => m.id === movie.id)) {
      return false;
    }
    movies.push(movie);
    // Sort by average_score descending
    movies.sort((a, b) => (b.average_score || 0) - (a.average_score || 0));
    this.saveAll(movies);
    return true;
  },

  addMany(newMovies) {
    const movies = this.getAll();
    const existingIds = new Set(movies.map((m) => m.id));
    let addedCount = 0;

    for (const movie of newMovies) {
      if (!existingIds.has(movie.id)) {
        movies.push(movie);
        existingIds.add(movie.id);
        addedCount++;
      }
    }

    // Sort by average_score descending
    movies.sort((a, b) => (b.average_score || 0) - (a.average_score || 0));
    this.saveAll(movies);
    return addedCount;
  },

  updateMovie(movieId, updates) {
    /**
     * Partially update a movie in storage.
     * Returns { movie, oldIndex, newIndex } or null if not found.
     */
    const movies = this.getAll();
    const oldIndex = movies.findIndex((m) => m.id === movieId);
    if (oldIndex === -1) return null;

    // Merge updates into existing movie
    const movie = { ...movies[oldIndex], ...updates };

    // Recalculate average score if ratings changed
    if (updates.imdb || updates.tmdb || updates.rt) {
      movie.average_score = this.calculateAverage(movie);
    }

    movies[oldIndex] = movie;

    // Re-sort by average_score descending
    movies.sort((a, b) => (b.average_score || 0) - (a.average_score || 0));

    // Find new index after sort
    const newIndex = movies.findIndex((m) => m.id === movieId);

    this.saveAll(movies);

    return { movie, oldIndex, newIndex };
  },

  calculateAverage(movie) {
    /**
     * Calculate average score from all available platform ratings.
     * Returns the average or 0 if no valid ratings.
     */
    const scores = [];

    if (movie.imdb && movie.imdb.rating && movie.imdb.rating > 0) {
      scores.push(movie.imdb.rating);
    }
    if (movie.tmdb && movie.tmdb.rating && movie.tmdb.rating > 0) {
      scores.push(movie.tmdb.rating);
    }
    if (movie.rt && movie.rt.rating && movie.rt.rating > 0) {
      scores.push(movie.rt.rating);
    }

    if (scores.length === 0) return 0;
    return Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10;
  },

  remove(movieId) {
    const movies = this.getAll();
    const filtered = movies.filter((m) => m.id !== movieId);
    if (filtered.length < movies.length) {
      this.saveAll(filtered);
      return true;
    }
    return false;
  },

  count() {
    return this.getAll().length;
  },
};
