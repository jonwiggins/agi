#!/bin/bash
set -e

# Docker entrypoint script for AGI Platform
# This script handles initialization and startup

echo "AGI Platform - Starting..."
echo "=========================="

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable is not set!"
    echo "Please set it in your .env file or docker-compose.yml"
    exit 1
fi

# Create data directories if they don't exist
echo "Creating data directories..."
mkdir -p "${CHROMA_PERSIST_DIRECTORY:-/app/data/chroma}"

# Verify Python packages
echo "Verifying Python environment..."
python -c "import anthropic, fastapi, chromadb" 2>/dev/null || {
    echo "ERROR: Required Python packages not found!"
    exit 1
}

echo "Environment check passed!"
echo "=========================="
echo "Configuration:"
echo "  Model: ${DEFAULT_MODEL:-claude-sonnet-4-5-20250929}"
echo "  Memory Collection: ${MEMORY_COLLECTION_NAME:-agi_memories}"
echo "  Max Memory Results: ${MAX_MEMORY_RESULTS:-5}"
echo "  Port: ${PORT:-8000}"
echo "=========================="

# Execute the main command
exec "$@"
