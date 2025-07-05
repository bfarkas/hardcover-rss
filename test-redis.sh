#!/bin/bash

# Test Redis Connectivity

echo "🔍 Testing Redis Connectivity"
echo "============================="

# Get Redis URL from environment or use default
REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}
echo "📡 Testing Redis URL: $REDIS_URL"

# Extract host and port from Redis URL
if [[ $REDIS_URL =~ redis://([^:]+):([0-9]+) ]]; then
    REDIS_HOST=${BASH_REMATCH[1]}
    REDIS_PORT=${BASH_REMATCH[2]}
    echo "   Host: $REDIS_HOST"
    echo "   Port: $REDIS_PORT"
else
    echo "❌ Invalid Redis URL format: $REDIS_URL"
    exit 1
fi

# Test basic connectivity
echo ""
echo "🔌 Testing basic connectivity..."

# Test if port is open
if nc -z "$REDIS_HOST" "$REDIS_PORT" 2>/dev/null; then
    echo "✅ Port $REDIS_PORT is open on $REDIS_HOST"
else
    echo "❌ Cannot connect to $REDIS_HOST:$REDIS_PORT"
    echo ""
    echo "🔧 Troubleshooting tips:"
    echo "   1. Make sure Redis is running"
    echo "   2. Check if Redis is listening on the correct port"
    echo "   3. Verify firewall settings"
    echo "   4. For Docker: ensure containers are on the same network"
    exit 1
fi

# Test Redis ping
echo ""
echo "🏓 Testing Redis ping..."
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
        echo "✅ Redis ping successful"
    else
        echo "❌ Redis ping failed"
        exit 1
    fi
else
    echo "⚠️  redis-cli not available, skipping ping test"
fi

# Test from Docker container if available
echo ""
echo "🐳 Testing from Docker container..."
if command -v docker >/dev/null 2>&1; then
    if docker run --rm redis:7-alpine redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
        echo "✅ Redis accessible from Docker container"
    else
        echo "❌ Redis not accessible from Docker container"
        echo ""
        echo "🔧 Docker troubleshooting:"
        echo "   1. Ensure containers are on the same network"
        echo "   2. Check if Redis is exposed to the Docker network"
        echo "   3. Try using 'host.docker.internal' for local Redis"
    fi
else
    echo "⚠️  Docker not available, skipping Docker test"
fi

echo ""
echo "✅ Redis connectivity test completed!" 