#!/bin/bash
# Wait for all services to be healthy

set -e

echo "Waiting for services to be healthy..."

services=("database" "redis" "mind")
max_wait=60
elapsed=0

all_healthy() {
    for service in "${services[@]}"; do
        if ! docker-compose ps | grep "$service" | grep -q "healthy\|Up"; then
            return 1
        fi
    done
    return 0
}

while [ $elapsed -lt $max_wait ]; do
    if all_healthy; then
        echo "✓ All services are healthy!"
        exit 0
    fi
    
    echo "Waiting... ($elapsed/$max_wait seconds)"
    sleep 2
    elapsed=$((elapsed + 2))
done

echo "❌ Services did not become healthy within $max_wait seconds"
docker-compose ps
exit 1
