#!/bin/bash

# Test Local Multi-Architecture Docker Build

echo "🏗️  Testing Local Multi-Architecture Docker Build"
echo "================================================="

# Check if Docker Buildx is available
echo "🔍 Checking Docker Buildx support..."
if docker buildx version >/dev/null 2>&1; then
    echo "✅ Docker Buildx is available"
else
    echo "❌ Docker Buildx not available"
    exit 1
fi

# Create a new builder instance for multi-arch
echo ""
echo "🔧 Setting up multi-arch builder..."
docker buildx create --name multiarch-builder --use 2>/dev/null || docker buildx use multiarch-builder

# Test building for multiple platforms
echo ""
echo "🏗️  Building multi-arch image locally..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag hardcover-rss:test-multiarch \
    --load \
    .

if [ $? -eq 0 ]; then
    echo "✅ Multi-arch build successful!"
    
    echo ""
    echo "🔍 Checking built image architecture support:"
    docker manifest inspect hardcover-rss:test-multiarch | grep -A 5 "architecture"
    
    echo ""
    echo "🧪 Testing the built image:"
    docker run --rm hardcover-rss:test-multiarch python -c "import platform; print('Platform:', platform.machine())"
    
    echo ""
    echo "🧹 Cleaning up test image..."
    docker rmi hardcover-rss:test-multiarch
else
    echo "❌ Multi-arch build failed"
    exit 1
fi

echo ""
echo "✅ Local multi-arch test completed!" 