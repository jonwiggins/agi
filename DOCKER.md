# Docker Deployment Guide

Comprehensive guide for deploying the AGI Platform using Docker.

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Architecture

### Container Structure

The AGI Platform runs in a single, optimized container with:
- Multi-stage Docker build for minimal image size
- Non-root user for security
- Health checks for reliability
- Volume mounts for persistent data

### Volumes

- **chroma-data**: Persistent ChromaDB vector database
- **Source code** (dev mode): Hot-reload during development

### Network

- Bridge network for container isolation
- Port 8000 exposed for API access

## Quick Start

### Prerequisites

- Docker 20.10 or higher
- Docker Compose 1.29 or higher
- 4GB+ RAM available for Docker
- Anthropic API key

### First Time Setup

```bash
# Clone and navigate to repository
git clone <repository-url>
cd agi

# Run setup
make setup

# Edit .env file with your API key
nano .env  # or vim, code, etc.
```

Add your API key to `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-...
```

### Start the Platform

```bash
# Build and start
make build
make up

# Check status
docker-compose ps

# View logs
make logs
```

### Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is 25 + 17?",
    "store_in_memory": false
  }'
```

## Configuration

### Environment Variables

All configuration is done via environment variables in `.env`:

```env
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional - Memory Configuration
CHROMA_PERSIST_DIRECTORY=/app/data/chroma
MEMORY_COLLECTION_NAME=agi_memories
MAX_MEMORY_RESULTS=5
MEMORY_RELEVANCE_THRESHOLD=0.7

# Optional - Agent Configuration
DEFAULT_MODEL=claude-sonnet-4-5-20250929

# Optional - Server Configuration
PORT=8000
HOST=0.0.0.0
```

### Resource Limits

Default resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '0.5'
      memory: 1G
```

Adjust these based on your workload:

```bash
# Edit docker-compose.yml
nano docker-compose.yml

# Restart to apply
make restart
```

## Development

### Hot-Reload Mode

For active development with automatic code reloading:

```bash
# Start in development mode
make dev-up

# Logs will stream automatically
# Code changes in src/ and tools/ will auto-reload
```

### Accessing the Container

```bash
# Open a shell
make shell

# Or use docker directly
docker-compose exec agi-platform /bin/bash
```

### Running Tests

```bash
# Run tests in container
make test

# Or manually
docker-compose exec agi-platform pytest -v
```

### Debugging

```bash
# View logs with timestamps
docker-compose logs -f --timestamps

# View specific container logs
docker-compose logs agi-platform

# Inspect container
docker inspect agi-platform

# Check resource usage
docker stats agi-platform
```

## Production Deployment

### Security Best Practices

1. **Use secrets management**:
   ```bash
   # Don't commit .env file
   # Use Docker secrets or environment injection
   docker secret create anthropic_key /path/to/key
   ```

2. **Run behind reverse proxy**:
   ```nginx
   # nginx.conf example
   server {
       listen 80;
       server_name api.yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Enable HTTPS**:
   - Use Let's Encrypt with certbot
   - Configure SSL termination at reverse proxy

4. **Restrict API access**:
   - Add authentication middleware
   - Implement rate limiting
   - Use API keys

### Scaling

For high-traffic deployments:

```bash
# Scale up replicas
docker-compose up -d --scale agi-platform=3

# Use load balancer
# Configure nginx upstream
```

### Backup and Restore

#### Backup ChromaDB Data

```bash
# Stop the container
make down

# Backup data directory
tar -czf chroma-backup-$(date +%Y%m%d).tar.gz data/chroma/

# Restart
make up
```

#### Restore ChromaDB Data

```bash
# Stop container
make down

# Restore backup
tar -xzf chroma-backup-YYYYMMDD.tar.gz

# Start container
make up
```

### Monitoring

#### Health Checks

The container includes automatic health checks:

```bash
# View health status
docker-compose ps

# Manual health check
curl http://localhost:8000/health
```

#### Logs

```bash
# Stream logs
docker-compose logs -f

# Export logs
docker-compose logs > app-logs-$(date +%Y%m%d).log
```

#### Metrics

Consider adding:
- Prometheus for metrics collection
- Grafana for visualization
- Loki for log aggregation

### Updates and Maintenance

```bash
# Pull latest code
git pull

# Rebuild image
make build

# Restart with new image
make down
make up

# Clean up old images
docker image prune -a
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs agi-platform

# Common issues:
# 1. Missing API key - check .env file
# 2. Port conflict - change PORT in .env
# 3. Insufficient resources - check docker stats
```

### API Returns Errors

```bash
# Check API key is valid
docker-compose exec agi-platform \
  python -c "import os; print('Key present:', bool(os.getenv('ANTHROPIC_API_KEY')))"

# Test Anthropic connection
docker-compose exec agi-platform \
  python -c "from src.api.client import AnthropicClient; \
             import os; \
             client = AnthropicClient(os.getenv('ANTHROPIC_API_KEY')); \
             print('Connection OK')"
```

### Memory/ChromaDB Issues

```bash
# Check data directory permissions
ls -la data/chroma/

# Reset ChromaDB (WARNING: deletes all memories)
make down
rm -rf data/chroma/*
make up
```

### Performance Issues

```bash
# Check resource usage
docker stats agi-platform

# Increase limits in docker-compose.yml
# Restart container
make restart
```

### Network Issues

```bash
# Check port binding
netstat -tulpn | grep 8000

# Test from within container
docker-compose exec agi-platform curl localhost:8000/health

# Check network
docker network inspect agi_agi-network
```

## Advanced Configuration

### Custom Docker Compose Override

Create `docker-compose.override.yml` for local customization:

```yaml
version: '3.8'

services:
  agi-platform:
    environment:
      - DEBUG=true
    ports:
      - "8001:8000"  # Use different port
```

### Multi-Container Setup

For production with dedicated services:

```yaml
# docker-compose.prod.yml
services:
  agi-platform:
    # ... existing config ...

  redis:
    image: redis:alpine
    volumes:
      - redis-data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## Support

For issues and questions:
- Check logs: `make logs`
- Review documentation
- Open an issue on GitHub
- Check Docker daemon status: `docker info`
