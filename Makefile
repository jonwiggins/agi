.PHONY: help build up down logs test clean dev prod status shell-mind shell-db

help:
	@echo "AGI Platform - Recursive Subagent Architecture"
	@echo ""
	@echo "Available commands:"
	@echo "  make build      - Build all containers"
	@echo "  make up         - Start the platform in production mode"
	@echo "  make dev        - Start the platform in development mode (hot-reload)"
	@echo "  make down       - Stop all containers"
	@echo "  make logs       - View logs from all containers"
	@echo "  make logs-mind  - View logs from mind container only"
	@echo "  make status     - Check status of all containers"
	@echo "  make test       - Run a test task"
	@echo "  make shell-mind - Open shell in mind container"
	@echo "  make shell-db   - Open PostgreSQL shell"
	@echo "  make clean      - Stop and remove all containers and volumes"
	@echo "  make reset      - Complete reset (clean + rebuild)"

build:
	docker-compose build

up:
	@echo "Starting AGI Platform in production mode..."
	docker-compose up -d
	@echo ""
	@echo "Platform started! Access points:"
	@echo "  - WebUI: http://localhost:3000"
	@echo "  - Mind API: http://localhost:8000"
	@echo "  - Health Check: http://localhost:8000/health"
	@echo "  - Database: localhost:5432"
	@echo ""
	@echo "View logs: make logs"

dev:
	@echo "Starting AGI Platform in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
	@echo ""
	@echo "Development mode access points:"
	@echo "  - WebUI: http://localhost:3000"
	@echo "  - Mind API: http://localhost:8000"
	@echo "  - pgAdmin: http://localhost:5050 (admin@agi.local / admin)"
	@echo "  - Redis Commander: http://localhost:8081"

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-mind:
	docker-compose logs -f mind

status:
	@echo "Container Status:"
	@docker-compose ps
	@echo ""
	@echo "Health Checks:"
	@docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $$(docker-compose ps -q) 2>/dev/null || true

test:
	@echo "Submitting test task..."
	@curl -X POST http://localhost:8000/tasks \
	  -H "Content-Type: application/json" \
	  -d '{"task": "Calculate the factorial of 5", "context": {}, "max_depth": 3}' | jq
	@echo ""
	@echo "Check task status with: curl http://localhost:8000/tasks/{task_id} | jq"

shell-mind:
	docker-compose exec mind /bin/bash

shell-db:
	docker-compose exec database psql -U agi -d agi_memory

clean:
	@echo "Stopping and removing all containers and volumes..."
	docker-compose down -v
	@echo "Cleanup complete!"

reset: clean build up
	@echo "Platform reset and restarted!"
