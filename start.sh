#!/bin/bash
set -e

echo "=========================================="
echo "  AGI Platform - Recursive Subagents"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after you've added your API key..."
fi

# Verify API key is set
if grep -q "your_api_key_here\|your_anthropic_key_here" .env; then
    echo "❌ Error: Please set your ANTHROPIC_API_KEY in .env file"
    exit 1
fi

echo "✓ Configuration found"
echo ""
echo "Building containers..."
docker-compose build

echo ""
echo "Starting platform..."
docker-compose up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 5

# Check health
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Mind service is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Mind service failed to start"
        docker-compose logs mind
        exit 1
    fi
    sleep 2
done

# Check WebUI
for i in {1..20}; do
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo "✓ WebUI service is healthy"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "⚠️  WebUI service failed to start (continuing anyway)"
        break
    fi
    sleep 2
done

echo ""
echo "=========================================="
echo "  🚀 AGI Platform is running!"
echo "=========================================="
echo ""
echo "Access Points:"
echo "  🌐 WebUI:         http://localhost:3000"
echo "  📡 Mind API:      http://localhost:8000"
echo "  🏥 Health Check:  http://localhost:8000/health"
echo "  📊 Stats:         http://localhost:8000/stats"
echo ""
echo "Quick Commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop platform:    docker-compose down"
echo "  View status:      docker-compose ps"
echo ""
echo "Example Task Submission:"
echo '  curl -X POST http://localhost:8000/tasks \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"task": "Explain recursion", "max_depth": 3}'"'"' | jq'
echo ""
echo "For more commands: make help"
echo ""
echo "Attaching to logs (Ctrl+C to exit, services will keep running)..."
echo ""
docker-compose logs -f
