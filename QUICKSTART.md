# Quick Start Guide

Get the AGI Platform running in under 5 minutes with Docker.

## Prerequisites

✅ Docker installed (20.10+)
✅ Docker Compose installed (1.29+)
✅ Anthropic API key ([Get one here](https://console.anthropic.com/))

## 3-Step Setup

### Step 1: Clone and Configure

```bash
git clone <repository-url>
cd agi
make setup
```

### Step 2: Add Your API Key

Edit `.env` and add your Anthropic API key:

```bash
# On Mac/Linux
nano .env

# Or use your preferred editor
code .env
vim .env
```

Add this line:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 3: Launch

```bash
make build
make up
```

## Verify It's Working

```bash
# Check health
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! What is 5 + 3?"}'

# Or run comprehensive tests
make test-docker
```

## Access the API

- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Common Commands

```bash
make logs        # View live logs
make status      # Check container status
make restart     # Restart the platform
make down        # Stop everything
make clean       # Full cleanup
```

## Development Mode

For hot-reloading during development:

```bash
make dev-up
# Edit code in src/ - changes auto-reload
# Press Ctrl+C to stop
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Try Examples**: Run `python example_usage.py` (requires .env setup)
3. **Create Custom Tools**: See `tools/examples.py` for reference
4. **Read Full Docs**: Check `README.md` and `DOCKER.md`

## Troubleshooting

### Can't connect to API?
```bash
# Check if running
make status

# View logs
make logs

# Restart
make restart
```

### Port 8000 already in use?
```bash
# Edit .env and change PORT
echo "PORT=8080" >> .env
make restart
```

### Out of memory?
```bash
# Edit docker-compose.yml and reduce limits
# Look for the 'deploy.resources' section
```

## Need Help?

- Check logs: `make logs`
- Full documentation: `README.md`
- Docker guide: `DOCKER.md`
- Open an issue on GitHub

## Stopping the Platform

```bash
# Stop containers (data preserved)
make down

# Stop and remove all data
make clean
```

That's it! Your AGI platform is now running. 🚀
