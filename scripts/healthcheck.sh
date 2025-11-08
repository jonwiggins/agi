#!/bin/bash
# Health check script for AGI Platform

# Try to connect to the health endpoint
response=$(curl -f -s http://localhost:8000/health 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed"
    exit 1
fi
