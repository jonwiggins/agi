# Quick Start Guide

Get the AGI Platform running in under 5 minutes!

## Prerequisites

- Docker 20.10+
- Docker Compose v2.40.3+ (plugin version)
- 8GB+ RAM
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Option 1: Automated Start (Recommended)

```bash
./start.sh
```

This script will:
1. Create `.env` from template if needed
2. Build all containers
3. Start the platform
4. Verify health
5. Show access points

## Option 2: Manual Start

### 1. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit and add your API key
nano .env
# Set: ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start

```bash
# Using Make
make up

# Or using Docker Compose directly
docker compose up -d
```

### 3. Verify

```bash
curl http://localhost:8000/health | jq
```

## Submit Your First Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a Python function to calculate Fibonacci numbers",
    "context": {
      "requirements": ["Use recursion", "Add type hints", "Include docstring"]
    },
    "max_depth": 5,
    "max_agents": 20
  }' | jq
```

Save the `task_id` from the response.

## Check Task Status

```bash
# Replace {task_id} with your actual task ID
curl http://localhost:8000/tasks/{task_id} | jq
```

## Watch Real-Time Progress

```bash
# Install wscat if needed: npm install -g wscat
wscat -c ws://localhost:8000/ws/tasks/{task_id}
```

## View Logs

```bash
# All logs
docker compose logs -f

# Mind only
docker compose logs -f mind

# Using Make
make logs
```

## Common Commands

```bash
# Check status
docker compose ps
make status

# View stats
curl http://localhost:8000/stats | jq

# Stop platform
docker compose down
make down

# Development mode (hot-reload)
make dev

# Test task
make test
```

## Development Mode

For development with hot-reload:

```bash
make dev
```

This starts:
- Mind API with auto-reload: http://localhost:8000
- pgAdmin: http://localhost:5050 (admin@agi.local / admin)
- Redis Commander: http://localhost:8081

## Troubleshooting

### Platform won't start

```bash
# Check logs
docker compose logs

# Reset everything
make reset
```

### API returns errors

```bash
# Check mind logs
docker compose logs mind

# Verify API key is set
grep ANTHROPIC_API_KEY .env
```

### Database connection issues

```bash
# Check database health
docker compose exec database pg_isready -U agi

# View database logs
docker compose logs database
```

## Example Tasks to Try

### Simple Tasks

```bash
# Math
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task": "What is 123 * 456?"}' | jq

# Information
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task": "Explain how binary search works"}' | jq
```

### Complex Tasks (Multiple Agents)

```bash
# API Design
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Design a REST API for a blog platform",
    "context": {"features": ["posts", "comments", "users", "tags"]},
    "max_depth": 8
  }' | jq

# System Architecture
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Design a scalable microservices architecture for e-commerce",
    "max_depth": 10,
    "max_agents": 50
  }' | jq
```

## Next Steps

- Read the full [README.md](README.md) for architecture details
- Explore the [API Reference](README.md#api-reference)
- Check out [Architecture Decisions](README.md#architecture-decisions)
- Learn about [Safety Mechanisms](README.md#safety-mechanisms)

## Clean Up

```bash
# Stop containers
docker compose down

# Remove everything (including volumes)
make clean
```

## Need Help?

- Check logs: `make logs`
- View status: `make status`
- See all commands: `make help`
- Review configuration: `cat .env`

Happy recursive problem-solving! 🚀
