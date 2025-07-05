# Hardcover RSS Service

A service that provides RSS feeds for Hardcover.app "want to read" lists, similar to Goodreads RSS feeds.

## Features

- 📚 Fetch "want to read" lists from Hardcover.app using the official GraphQL API
- 📡 Generate RSS feeds in Goodreads format
- 🔄 Automatic background refresh (configurable interval)
- 💾 Redis caching for improved performance
- 🚀 RESTful API for managing users
- 🐳 Docker containerization
- 📊 Health monitoring endpoints

## Quick Start

### Using Docker Compose (Recommended)

#### Option 1: Using Pre-built Images (Fastest)

1. Clone the repository:
```bash
git clone <repository-url>
cd hardcover_rss
```

2. Set up your environment variables:
```bash
# Copy the example environment file
cp env.example .env

# Edit .env and add your Hardcover API token
# Get your token from https://hardcover.app/settings/api
```

3. Start the service with pre-built images:
```bash
./deploy.sh
```

#### Option 2: Building Locally

1. Clone the repository:
```bash
git clone <repository-url>
cd hardcover_rss
```

2. Set up your environment variables:
```bash
# Copy the example environment file
cp env.example .env

# Edit .env and add your Hardcover API token
# Get your token from https://hardcover.app/settings/api
```

3. Build and start the service:
```bash
docker-compose up -d
```

3. Add a user to track:
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_hardcover_username"}'
```

4. Access the RSS feed:
```
http://localhost:8000/feed/your_hardcover_username
```

### Using Docker Run

1. Build the image:
```bash
docker build -t hardcover-rss .
```

2. Run with Redis:
```bash
# Start Redis
docker run -d --name redis redis:7-alpine

# Start the service (replace 'your_token_here' with your actual token)
docker run -d --name hardcover-rss \
  -p 8000:8000 \
  -e HARDCOVER_API_TOKEN="your_token_here" \
  -e REDIS_URL="redis://host.docker.internal:6379" \
  hardcover-rss
```

**Note**: For production use, consider using environment files or Docker secrets instead of passing tokens directly in the command line.

## API Endpoints

### User Management

- `POST /users` - Add a new user to track
- `GET /users` - List all registered users
- `DELETE /users/{username}` - Remove a user from tracking

### RSS Feeds

- `GET /feed/{username}` - Get RSS feed for a specific user
- `GET /feeds` - List all available feeds

### Management

- `GET /health` - Health check and status
- `POST /refresh/{username}` - Manually refresh a user's feed
- `POST /refresh` - Manually refresh all feeds

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HARDCOVER_API_TOKEN` | Your Hardcover API token | Required |
| `HARDCOVER_API_URL` | Hardcover GraphQL API URL | `https://api.hardcover.app/v1/graphql` |
| `REFRESH_INTERVAL` | Background refresh interval (seconds) | `3600` |
| `CACHE_TTL` | Cache TTL (seconds) | `1800` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |

### Example Environment File

Copy `env.example` to `.env` and update with your values:
```bash
cp env.example .env
```

Example `.env` file:
```env
HARDCOVER_API_TOKEN=your_token_here
REFRESH_INTERVAL=3600
CACHE_TTL=1800
LOG_LEVEL=INFO
REDIS_URL=redis://redis:6379
```

**Security Note**: Never commit your `.env` file to version control. The `.env` file is already included in `.gitignore`.

## Usage Examples

### Adding a User

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "display_name": "John Doe"
  }'
```

### Getting RSS Feed

```bash
curl "http://localhost:8000/feed/john_doe"
```

### Checking Health

```bash
curl "http://localhost:8000/health"
```

## RSS Feed Format

The service generates RSS feeds in a format similar to Goodreads, including:

- Book title and author
- Book description
- Publication year and page count
- Average rating
- Date added to want-to-read list
- Direct links to Hardcover book pages

## Development

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export HARDCOVER_API_TOKEN="your_token_here"
export REDIS_URL="redis://localhost:6379"
```

3. Start Redis:
```bash
docker run -d --name redis redis:7-alpine
```

4. Run the service:
```bash
python -m uvicorn app.main:app --reload
```

### Testing

The service includes health checks and error handling. You can test the API using the interactive documentation at `http://localhost:8000/docs`.

## Docker Images

Pre-built Docker images are available on GitHub Container Registry:

```bash
# Pull the latest image (recommended)
docker pull ghcr.io/bfarkas/hardcover-rss:latest

# Or use a specific version
docker pull ghcr.io/bfarkas/hardcover-rss:v1.0.0

# Or use the main branch
docker pull ghcr.io/bfarkas/hardcover-rss:main
```

### Available Tags

- `latest` - Latest stable release (same as main branch)
- `main` - Latest commit on main branch
- `v*` - Versioned releases (e.g., `v1.0.0`, `v1.1.0`)
- `main-<sha>` - Specific commit builds

### Running with Docker Run

```bash
# Start Redis
docker run -d --name redis redis:7-alpine

# Start the service
docker run -d --name hardcover-rss \
  -p 8000:8000 \
  -e HARDCOVER_API_TOKEN="your_token_here" \
  -e REDIS_URL="redis://host.docker.internal:6379" \
  ghcr.io/bfarkas/hardcover-rss:latest
```

## Architecture

- **FastAPI**: Web framework for the REST API
- **GraphQL**: Communication with Hardcover API
- **Redis**: Caching layer for user data
- **APScheduler**: Background job scheduling
- **Feedgen**: RSS feed generation
- **Docker**: Containerization

## Monitoring

The service provides several monitoring endpoints:

- `/health` - Overall service health
- Cache statistics
- Scheduler job status
- Registered user count

## Troubleshooting

### Common Issues

1. **User not found**: Ensure the username exists on Hardcover.app
2. **API token issues**: Verify your Hardcover API token is valid
3. **Redis connection**: Check Redis is running and accessible
4. **Rate limiting**: The service includes delays between API calls

### Logs

Check the service logs:
```bash
docker-compose logs hardcover-rss
```

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request 