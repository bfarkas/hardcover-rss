# Docker Registry Options

This guide covers different options for publishing Docker images for your Hardcover RSS Service.

## 🏆 Recommended: GitHub Container Registry (ghcr.io)

**Best for**: Open source projects, GitHub-hosted repositories

### Advantages
- ✅ Free for public repositories
- ✅ Integrated with GitHub Actions
- ✅ Modern container registry
- ✅ Good security features
- ✅ No setup required for GitHub repos

### Configuration
The repository includes a GitHub Actions workflow (`.github/workflows/docker-publish.yml`) that automatically:
- Builds images on every push to `main`
- Publishes to `ghcr.io/yourusername/hardcover_rss`
- Creates versioned tags for releases

### Usage
```bash
# Pull the image
docker pull ghcr.io/yourusername/hardcover_rss:latest

# Use in docker-compose
image: ghcr.io/yourusername/hardcover_rss:latest
```

## 🐳 Docker Hub

**Best for**: Maximum visibility, wide distribution

### Advantages
- ✅ Most popular container registry
- ✅ Free for public repositories
- ✅ Excellent discoverability
- ✅ Large community

### Setup
1. Create account at [hub.docker.com](https://hub.docker.com)
2. Create a repository named `hardcover-rss`
3. Update the GitHub Actions workflow:

```yaml
# In .github/workflows/docker-publish.yml
env:
  REGISTRY: docker.io
  IMAGE_NAME: yourusername/hardcover_rss

# Update login step
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}
```

4. Add secrets in GitHub repository settings:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub access token

### Usage
```bash
# Pull the image
docker pull yourusername/hardcover_rss:latest

# Use in docker-compose
image: yourusername/hardcover_rss:latest
```

## ☁️ Google Container Registry (gcr.io)

**Best for**: Google Cloud users, enterprise environments

### Advantages
- ✅ Free tier available
- ✅ Good integration with GCP services
- ✅ Enterprise-grade security
- ✅ Global distribution

### Setup
1. Enable Container Registry API in Google Cloud Console
2. Create a service account with Storage Admin role
3. Download the service account key
4. Update GitHub Actions workflow:

```yaml
# In .github/workflows/docker-publish.yml
env:
  REGISTRY: gcr.io
  IMAGE_NAME: your-project-id/hardcover_rss

# Update login step
- name: Log in to Google Container Registry
  uses: docker/login-action@v3
  with:
    registry: gcr.io
    username: _json_key
    password: ${{ secrets.GCR_JSON_KEY }}
```

5. Add `GCR_JSON_KEY` secret with your service account key

### Usage
```bash
# Pull the image
docker pull gcr.io/your-project-id/hardcover_rss:latest

# Use in docker-compose
image: gcr.io/your-project-id/hardcover_rss:latest
```

## 🚀 Amazon Elastic Container Registry (ECR)

**Best for**: AWS users, enterprise environments

### Advantages
- ✅ Free tier available
- ✅ Excellent AWS integration
- ✅ Advanced security features
- ✅ Global distribution

### Setup
1. Create ECR repository in AWS Console
2. Create IAM user with ECR permissions
3. Generate access keys
4. Update GitHub Actions workflow:

```yaml
# In .github/workflows/docker-publish.yml
env:
  REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ secrets.AWS_REGION }}.amazonaws.com
  IMAGE_NAME: hardcover_rss

# Update login step
- name: Log in to Amazon ECR
  id: login-ecr
  uses: aws-actions/amazon-ecr-login@v2

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ steps.login-ecr.outputs.registry }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

5. Add AWS secrets in GitHub repository settings

### Usage
```bash
# Pull the image
docker pull your-account-id.dkr.ecr.region.amazonaws.com/hardcover_rss:latest

# Use in docker-compose
image: your-account-id.dkr.ecr.region.amazonaws.com/hardcover_rss:latest
```

## 🔧 Multi-Registry Setup

You can publish to multiple registries simultaneously by updating the GitHub Actions workflow:

```yaml
# Build once, push to multiple registries
- name: Build image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: false
    tags: |
      ghcr.io/yourusername/hardcover_rss:latest
      docker.io/yourusername/hardcover_rss:latest
    outputs: type=docker,dest=/tmp/image.tar

- name: Push to GitHub Container Registry
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/yourusername/hardcover_rss:latest

- name: Push to Docker Hub
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: docker.io/yourusername/hardcover_rss:latest
```

## 📊 Registry Comparison

| Registry | Free Tier | Setup Complexity | Discoverability | AWS Integration | GCP Integration |
|----------|-----------|------------------|-----------------|-----------------|-----------------|
| GitHub Container Registry | ✅ Public repos | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| Docker Hub | ✅ Public repos | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| Google Container Registry | ✅ 0.5GB/month | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Amazon ECR | ✅ 500MB/month | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

## 🎯 Recommendation

For your Hardcover RSS Service, I recommend:

1. **Start with GitHub Container Registry** - Easy setup, good for open source
2. **Add Docker Hub later** - For maximum visibility and discoverability
3. **Consider cloud-specific registries** - If you're heavily invested in AWS/GCP

The included GitHub Actions workflow is configured for GitHub Container Registry by default, but can be easily modified for other registries. 