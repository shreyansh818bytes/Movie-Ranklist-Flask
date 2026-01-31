# Movie Ranklist

A web application to create and manage your personal movie rankings. Search for movies, view ratings from multiple platforms (IMDb, TMDb, Rotten Tomatoes), and organize them in a ranked list.

## Features

- Search movies by title and year
- View ratings from IMDb, TMDb, and Rotten Tomatoes
- Automatic average score calculation
- Drag-and-drop ranking with smooth animations
- User authentication
- Responsive design with dark theme

## Tech Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Vanilla JS, Bootstrap 5
- **Containerization**: Docker, Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose
- API keys for [IMDb (RapidAPI)](https://rapidapi.com/apidojo/api/imdb8) and [TMDb](https://www.themoviedb.org/settings/api)

### Environment Setup

Create the environment file at `config/.env.local` and add the following content:

```env
# Server Configuration
PORT=8000
FLASK_DEBUG=false

# Database (optional - defaults to SQLite if not set)
# DATABASE_URL=postgresql://movieapp:movieapp@db:5432/movieapp

# Security (required - generate a secure random string)
SECRET_KEY=your-secret-key-here

# API Keys (required)
IMDB_API_KEY=your-imdb-rapidapi-key
TMDB_API_KEY=your-tmdb-api-key
```

### Running the Application

Start the application with Docker Compose:

```bash
docker-compose up
```

The app will be available at http://localhost:8000

To run in detached mode:

```bash
docker-compose up -d
```

To stop the application:

```bash
docker-compose down
```

### Development Mode

For development with hot reload, set `FLASK_DEBUG=true` in your `.env.local` file. The docker-compose configuration already sets this to `1` by default.

## Project Structure

```
.
├── app.py                 # Flask application entry point
├── config/
│   └── .env.local         # Environment variables (not committed)
├── static/
│   ├── js/                # Frontend JavaScript
│   └── styles/            # CSS styles
├── templates/             # Jinja2 HTML templates
├── utils/
│   ├── api/               # External API integrations
│   ├── auth.py            # Authentication logic
│   ├── env_variables.py   # Environment configuration
│   ├── helpers.py         # Helper functions
│   └── models.py          # Database models
└── tests/                 # Test suite
```

## Contributing

Contributions are welcome—feel free to open issues or submit pull requests.

## License

MIT
