#!/bin/bash
# Test script for Docker deployment

set -e

echo "======================================"
echo "AGI Platform - Docker Deployment Test"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print info
info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Wait for service to be ready
wait_for_service() {
    info "Waiting for service to be ready..."
    for i in {1..30}; do
        if curl -s "${BASE_URL}/health" > /dev/null 2>&1; then
            success "Service is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    error "Service did not become ready in time"
    return 1
}

# Test 1: Check if container is running
echo "Test 1: Container Status"
if docker-compose ps | grep -q "agi-platform.*Up"; then
    success "Container is running"
else
    error "Container is not running"
    exit 1
fi
echo ""

# Test 2: Wait for service
echo "Test 2: Service Availability"
if wait_for_service; then
    echo ""
else
    exit 1
fi

# Test 3: Health endpoint
echo "Test 3: Health Check"
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    success "Health endpoint OK: $HEALTH_RESPONSE"
else
    error "Health endpoint failed: $HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 4: Root endpoint
echo "Test 4: Root Endpoint"
ROOT_RESPONSE=$(curl -s "${BASE_URL}/")
if echo "$ROOT_RESPONSE" | grep -q "AGI Platform"; then
    success "Root endpoint OK"
else
    error "Root endpoint failed"
    exit 1
fi
echo ""

# Test 5: Tools endpoint
echo "Test 5: Tools Endpoint"
TOOLS_RESPONSE=$(curl -s "${BASE_URL}/tools")
if echo "$TOOLS_RESPONSE" | grep -q "tools"; then
    TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
    success "Tools endpoint OK (${TOOL_COUNT} tools registered)"
else
    error "Tools endpoint failed"
    exit 1
fi
echo ""

# Test 6: Chat endpoint with simple message
echo "Test 6: Chat Endpoint (Simple)"
CHAT_RESPONSE=$(curl -s -X POST "${BASE_URL}/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello", "store_in_memory": false}')

if echo "$CHAT_RESPONSE" | grep -q "response"; then
    success "Chat endpoint OK"
    info "Response preview: $(echo "$CHAT_RESPONSE" | head -c 100)..."
else
    error "Chat endpoint failed"
    echo "$CHAT_RESPONSE"
    exit 1
fi
echo ""

# Test 7: Chat endpoint with tool usage
echo "Test 7: Chat Endpoint (With Tools)"
CALC_RESPONSE=$(curl -s -X POST "${BASE_URL}/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "What is 42 multiplied by 17?", "store_in_memory": false}')

if echo "$CALC_RESPONSE" | grep -q "tool_calls"; then
    success "Tool execution test OK"
    # Check if calculator was used
    if echo "$CALC_RESPONSE" | grep -q "calculator"; then
        info "Calculator tool was used"
    fi
else
    error "Tool execution test failed"
    exit 1
fi
echo ""

# Test 8: Memory operations
echo "Test 8: Memory Operations"
# Add memory
MEMORY_ADD=$(curl -s -X POST "${BASE_URL}/memory" \
    -H "Content-Type: application/json" \
    -d '{"content": "Test memory for Docker deployment", "metadata": {"test": true}}')

if echo "$MEMORY_ADD" | grep -q "memory_id"; then
    MEMORY_ID=$(echo "$MEMORY_ADD" | grep -o '"memory_id":"[^"]*"' | cut -d'"' -f4)
    success "Memory add OK (ID: $MEMORY_ID)"
else
    error "Memory add failed"
    exit 1
fi

# Search memory
MEMORY_SEARCH=$(curl -s -X POST "${BASE_URL}/memory/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "Docker deployment", "n_results": 5}')

if echo "$MEMORY_SEARCH" | grep -q "memories"; then
    success "Memory search OK"
else
    error "Memory search failed"
    exit 1
fi
echo ""

# Test 9: OpenAPI docs
echo "Test 9: API Documentation"
DOCS_RESPONSE=$(curl -s "${BASE_URL}/docs")
if echo "$DOCS_RESPONSE" | grep -q "swagger"; then
    success "API documentation is available at ${BASE_URL}/docs"
else
    error "API documentation failed"
    exit 1
fi
echo ""

# Summary
echo "======================================"
echo -e "${GREEN}All tests passed!${NC}"
echo "======================================"
echo ""
echo "The AGI Platform is running successfully!"
echo "Access points:"
echo "  - API: ${BASE_URL}"
echo "  - Docs: ${BASE_URL}/docs"
echo "  - Health: ${BASE_URL}/health"
echo ""
echo "View logs with: make logs"
echo "Stop with: make down"
