#!/bin/bash

# Hardcover RSS Service Setup Script

echo "🎯 Hardcover RSS Service Setup"
echo "=============================="

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Skipping environment setup."
else
    echo "📝 Setting up environment variables..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Created .env file from env.example"
        echo ""
        echo "🔧 Next steps:"
        echo "1. Edit .env and add your Hardcover API token"
        echo "2. Get your token from https://hardcover.app/settings/api"
        echo "3. Run: docker-compose up -d"
    else
        echo "❌ env.example not found. Please create .env manually."
    fi
fi

echo ""
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "🎉 Setup complete!"
echo "📊 Service should be running at http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/docs"
echo ""
echo "💡 To add a user, run:"
echo "curl -X POST 'http://localhost:8000/users' -H 'Content-Type: application/json' -d '{\"username\": \"your_username\"}'" 