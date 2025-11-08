.PHONY: help build up down restart logs clean dev-up dev-down test shell test-docker status webui webui-down

# Default target
help:
	@echo "AGI Platform - Docker Commands"
	@echo "==============================="
	@echo "Production:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start backend only"
	@echo "  make webui      - Start full stack (backend + Web UI)"
	@echo "  make down       - Stop the platform"
	@echo "  make webui-down - Stop full stack"
	@echo "  make restart    - Restart the platform"
	@echo "  make logs       - View logs"
	@echo "  make status     - Show container status"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up     - Start with hot-reload"
	@echo "  make dev-down   - Stop development"
	@echo ""
	@echo "Utilities:"
	@echo "  make shell      - Open shell in container"
	@echo "  make test       - Run pytest in container"
	@echo "  make test-docker - Test Docker deployment"
	@echo "  make clean      - Clean up containers and volumes"

# Production commands
build:
	docker-compose build

up:
	docker-compose up -d

webui:
	docker-compose -f docker-compose.full.yml up -d
	@echo ""
	@echo "✅ Full stack started!"
	@echo "🌐 Web UI: http://localhost:3000"
	@echo "📡 API: http://localhost:8000"
	@echo ""
	@echo "View logs: make logs"

webui-down:
	docker-compose -f docker-compose.full.yml down

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose -f docker-compose.full.yml logs -f 2>/dev/null || docker-compose logs -f

# Development commands
dev-up:
	docker-compose -f docker-compose.dev.yml up

dev-down:
	docker-compose -f docker-compose.dev.yml down

# Utility commands
shell:
	docker-compose exec agi-platform /bin/bash

test:
	docker-compose exec agi-platform pytest

test-docker:
	@echo "Running Docker deployment tests..."
	@bash scripts/test_docker.sh

status:
	@echo "Container Status:"
	@docker-compose ps
	@echo ""
	@echo "Resource Usage:"
	@docker stats --no-stream agi-platform 2>/dev/null || echo "Container not running"

clean:
	docker-compose down -v
	docker system prune -f

# First time setup
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please edit it with your ANTHROPIC_API_KEY"; \
	else \
		echo ".env file already exists"; \
	fi
	@mkdir -p data/chroma
	@echo "Setup complete! Run 'make up' to start the platform"
