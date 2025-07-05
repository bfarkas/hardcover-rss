# Deployment Guide

## Security Checklist ✅

Before deploying to GitHub, ensure the following:

- [x] **API Token Removed**: Real Hardcover API token removed from `docker-compose.yml`
- [x] **Environment Variables**: Using `${HARDCOVER_API_TOKEN}` placeholder
- [x] **Example File**: Created `env.example` for user reference
- [x] **Gitignore**: `.env` files are properly ignored
- [x] **Documentation**: Updated README with security notes

## GitHub Repository Setup

### 1. Initialize Git Repository

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Hardcover RSS Service

- FastAPI service for generating RSS feeds from Hardcover want-to-read lists
- Docker support with Redis caching
- Background scheduling for automatic refresh
- GraphQL integration with Hardcover API
- Multi-user support with API management"
```

### 2. Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. **Important**: Do NOT initialize with README, .gitignore, or license (we already have these)
3. Copy the repository URL

### 3. Push to GitHub

```bash
# Add remote origin
git remote add origin <your-github-repo-url>

# Push to GitHub
git push -u origin main
```

### 4. Enable GitHub Actions

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Actions** → **General**
3. Enable "Allow all actions and reusable workflows"
4. Save the changes

### 5. Publish Docker Images

The GitHub Actions workflow will automatically:
- Build Docker images on every push to `main`
- Publish images to GitHub Container Registry
- Create versioned tags for releases

To create a release:
```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

This will trigger the workflow to build and publish `ghcr.io/yourusername/hardcover_rss:v1.0.0`

## Environment Setup for Users

### Quick Start

```bash
# Clone the repository
git clone <your-github-repo-url>
cd hardcover_rss

# Run the setup script
./setup.sh
```

### Manual Setup

```bash
# Clone the repository
git clone <your-github-repo-url>
cd hardcover_rss

# Copy environment example
cp env.example .env

# Edit .env and add your API token
# Get token from: https://hardcover.app/settings/api

# Start services
docker-compose up -d
```

## Security Notes

### For Repository Owners

- ✅ API tokens are never committed to the repository
- ✅ Environment variables use placeholders
- ✅ `.env` files are in `.gitignore`
- ✅ Example files show proper configuration

### For Users

- 🔒 Always use `.env` files for sensitive data
- 🔒 Never commit your `.env` file
- 🔒 Use Docker secrets in production
- 🔒 Rotate API tokens regularly

## Production Deployment

### Environment Variables

For production, consider using:

1. **Docker Secrets** (Docker Swarm)
2. **Kubernetes Secrets**
3. **Environment files** (not in version control)
4. **Cloud provider secret management** (AWS Secrets Manager, etc.)

### Example Production docker-compose.yml

```yaml
services:
  hardcover-rss:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HARDCOVER_API_TOKEN_FILE=/run/secrets/hardcover_token
    secrets:
      - hardcover_token
    # ... other config

secrets:
  hardcover_token:
    file: ./secrets/hardcover_token.txt
```

## Monitoring

- Health check endpoint: `GET /health`
- API documentation: `GET /docs`
- Service logs: `docker-compose logs hardcover-rss`

## Support

For issues or questions:
1. Check the README.md for troubleshooting
2. Review the API documentation at `/docs`
3. Check service logs for errors
4. Verify your API token is valid 