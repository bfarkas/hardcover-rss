#!/bin/bash

# Check GitHub Actions Workflow Status

echo "🔍 Checking GitHub Actions Workflow Status"
echo "=========================================="

# Get the latest commit hash
COMMIT_HASH=$(git rev-parse HEAD)
echo "📝 Latest commit: $COMMIT_HASH"

# Check if the workflow is running
echo ""
echo "🔄 Checking workflow status..."
echo "   Visit: https://github.com/bfarkas/hardcover-rss/actions"
echo ""

# Try to pull the latest image with different tags
echo "📥 Testing different image tags:"

TAGS=("main" "latest" "main-$COMMIT_HASH" "main-$(git rev-parse --short HEAD)")

for tag in "${TAGS[@]}"; do
    echo "   Trying: ghcr.io/bfarkas/hardcover-rss:$tag"
    if docker pull ghcr.io/bfarkas/hardcover-rss:$tag >/dev/null 2>&1; then
        echo "   ✅ Success: ghcr.io/bfarkas/hardcover-rss:$tag"
        echo "   📊 Architecture support:"
        docker manifest inspect ghcr.io/bfarkas/hardcover-rss:$tag | grep -A 2 "architecture" | head -6
        break
    else
        echo "   ❌ Not found: ghcr.io/bfarkas/hardcover-rss:$tag"
    fi
done

echo ""
echo "💡 If no images are found, the workflow might still be running."
echo "   Check the Actions tab in your GitHub repository." 