#!/bin/bash

# Hardcover RSS Service Deployment Script
# Uses pre-built Docker images from GitHub Container Registry

echo "🚀 Hardcover RSS Service Deployment"
echo "==================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Setting up environment variables..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env file from env.example"
        echo ""
        echo "🔧 Please edit .env and add your Hardcover API token:"
        echo "   Get your token from https://hardcover.app/settings/api"
        echo ""
        read -p "Press Enter after you've updated .env..."
    else
        echo "❌ env.example not found. Please create .env manually."
        exit 1
    fi
fi

echo ""
echo "🐳 Starting services with pre-built Docker images..."
echo "   Using: ghcr.io/bfarkas/hardcover-rss:latest"

# Use the production compose file
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "🎉 Deployment complete!"
echo "📊 Service should be running at http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "💡 To add a user, run:"
echo "curl -X POST 'http://localhost:8000/users' -H 'Content-Type: application/json' -d '{\"username\": \"your_username\"}'"
echo ""
echo "📋 To check logs:"
echo "docker-compose -f docker-compose.prod.yml logs hardcover-rss" 