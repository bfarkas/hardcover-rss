#!/bin/bash

# Test Multi-Architecture Docker Image Support

echo "🐳 Testing Multi-Architecture Docker Image Support"
echo "=================================================="

# Get the latest image tag
IMAGE_NAME="ghcr.io/bfarkas/hardcover-rss:main"

echo "🔍 Available image tags:"
docker images ghcr.io/bfarkas/hardcover-rss --format "table {{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>/dev/null || echo "   No local images found"

echo "📥 Pulling multi-arch image: $IMAGE_NAME"
docker pull $IMAGE_NAME

echo ""
echo "🔍 Checking image architecture support:"
docker manifest inspect $IMAGE_NAME | grep -A 5 "architecture"

echo ""
echo "🏗️  Testing build for different platforms:"

# Test AMD64
echo "   Testing AMD64..."
docker run --rm --platform linux/amd64 $IMAGE_NAME python -c "import platform; print('AMD64:', platform.machine())" 2>/dev/null || echo "   ❌ AMD64 not supported"

# Test ARM64
echo "   Testing ARM64..."
docker run --rm --platform linux/arm64 $IMAGE_NAME python -c "import platform; print('ARM64:', platform.machine())" 2>/dev/null || echo "   ❌ ARM64 not supported"

echo ""
echo "✅ Multi-architecture test completed!"
echo ""
echo "💡 To run the service on your platform:"
echo "   docker run -p 8000:8000 -e HARDCOVER_API_TOKEN=your_token $IMAGE_NAME" 