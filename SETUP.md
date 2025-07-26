# Container Terminal Orchestrator - Setup Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Development Setup](#development-setup)
4. [Containerized Development (Recommended)](#containerized-development-recommended)
5. [Docker Setup](#docker-setup)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows (with Docker Desktop)
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Python**: Version 3.9 or higher (for local development only)
- **Node.js**: Version 18 or higher (for local development only)
- **Memory**: Minimum 4GB RAM
- **Storage**: At least 2GB free space

### Required Tools

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# For local development only:
# Check Python version
python --version

# Check Node.js version
node --version

# Install UV package manager (for local development)
pip install uv
```

## Installation Methods

### Method 1: Quick Start with Containerized Development (Recommended)

This method runs everything in Docker containers, avoiding platform-specific issues:

```bash
# Clone repository
git clone https://github.com/joshcassell4/docorcpty.git
cd docorcpty

# Start containerized development environment
make docker-dev

# Access the application
# API: http://localhost:8000
# Dashboard: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Method 2: Production Deployment

```bash
# Clone repository
git clone https://github.com/joshcassell4/docorcpty.git
cd docorcpty

# Build and start production containers
make docker-build
make docker-up
```

### Method 3: Local Development (Advanced)

**Note**: Local development may encounter platform-specific issues. We recommend using containerized development instead.

```bash
# Clone repository
git clone https://github.com/joshcassell4/docorcpty.git
cd docorcpty

# Install Python dependencies with UV
uv pip install -e ".[dev]"

# Install frontend dependencies
cd dashboard
npm install
cd ..

# Copy environment file
cp .env.sample .env

# Start development servers
make dev
```

## Development Setup

### Containerized Development (Recommended)

The containerized development environment provides the best experience across all platforms:

1. **Start Development Environment**:
```bash
# Start all services with hot-reloading
make docker-dev

# Or start in background
make docker-dev-up
```

2. **Access Container Shell**:
```bash
# Open shell in orchestrator container
make docker-dev-shell

# Run commands inside container
pytest                    # Run tests
ruff check .             # Run linter
mypy orchestrator        # Type checking
```

3. **View Logs**:
```bash
make docker-dev-logs
```

4. **Stop Environment**:
```bash
make docker-dev-down
```

See [DOCKER_DEV.md](DOCKER_DEV.md) for detailed containerized development documentation.

### Local Development

If you prefer local development despite potential platform issues:

#### Backend Development

1. **Install Dependencies**:
```bash
# Install development dependencies
make install-dev
```

2. **Run Tests**:
```bash
# Run all tests
make test

# Run with coverage
make test-coverage
```

3. **Start Backend Only**:
```bash
make run-dev
```

#### Frontend Development

1. **Install Dependencies**:
```bash
make frontend-install
```

2. **Start Frontend Dev Server**:
```bash
make frontend-dev
```

3. **Build for Production**:
```bash
make frontend-build
```

### Using UV for Dependency Management

```bash
# Install all dependencies (including dev)
uv pip install -e ".[dev]"

# Install production dependencies only
uv pip install -e .

# Add a new dependency
# Edit pyproject.toml manually, then:
uv pip install -e .
```

## Docker Setup

### Available Docker Commands

```bash
# Production Commands
make docker-build        # Build production images
make docker-up          # Start production containers
make docker-down        # Stop production containers
make docker-logs        # View production logs
make docker-shell       # Shell into production container

# Development Commands (Recommended)
make docker-dev         # Start dev environment with live reload
make docker-dev-build   # Build development images
make docker-dev-up      # Start dev containers in background
make docker-dev-down    # Stop dev containers
make docker-dev-logs    # View dev logs
make docker-dev-shell   # Shell into dev container
make docker-dev-restart # Restart dev containers
make docker-dev-clean   # Clean dev environment
```

### Docker Socket Access

The orchestrator needs access to the Docker socket:

**Windows (Docker Desktop)**: Works automatically

**Linux**:
```bash
# Option 1: Add user to docker group (recommended)
sudo usermod -aG docker $USER
# Log out and back in

# Option 2: Temporary fix
sudo chmod 666 /var/run/docker.sock
```

**macOS (Docker Desktop)**: Works automatically

## Configuration

### Environment Variables

Create a `.env` file from the sample:

```bash
cp .env.sample .env
```

Key environment variables:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Docker Configuration
DOCKER_SOCKET=/var/run/docker.sock
DOCKER_NETWORK=cto_network

# Resource Limits
MAX_CONCURRENT_SESSIONS=50
CONTAINER_CPU_LIMIT=1.0
CONTAINER_MEMORY_LIMIT=512m
SESSION_TIMEOUT_SECONDS=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Development
DEVELOPMENT=true
DEBUG=false
```

### Container Configuration

Container templates are stored in `configs/containers/`. To add a new template:

1. Create a JSON file in `configs/containers/`:
```json
{
  "name": "my-container",
  "image": "ubuntu:22.04",
  "command": "/bin/bash",
  "environment": {
    "MY_VAR": "value"
  },
  "volumes": ["./data:/data"],
  "resources": {
    "memory": "256m",
    "cpu_shares": 512
  }
}
```

2. Restart the orchestrator to load the new configuration.

## Troubleshooting

### Common Issues

#### Windows: ModuleNotFoundError: No module named 'fcntl'

**Error**: `ModuleNotFoundError: No module named 'fcntl'`

**Solution**: Use containerized development instead:
```bash
make docker-dev
```

The `fcntl` module is Linux-specific. Running in Docker containers avoids this issue.

#### Docker Socket Permission Denied

**Error**: `Permission denied while trying to connect to Docker daemon socket`

**Solution**:
```bash
# On Linux
sudo usermod -aG docker $USER
# Log out and back in

# Or temporarily
sudo chmod 666 /var/run/docker.sock
```

#### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Change port in .env or docker-compose.dev.yml
```

#### UV Command Errors

**Error**: `error: unexpected argument '--dev' found`

**Solution**: Use the correct UV syntax:
```bash
# Correct
uv pip install -e ".[dev]"

# Incorrect (old syntax)
uv pip sync --dev
```

#### Hatchling Build Errors

**Error**: `ValueError: Unable to determine which files to ship inside the wheel`

**Solution**: Ensure `pyproject.toml` has:
```toml
[tool.hatch.build.targets.wheel]
packages = ["orchestrator"]
```

### Platform-Specific Issues

#### Windows Development
- Use containerized development to avoid compatibility issues
- If using WSL2, ensure Docker Desktop is configured for WSL2
- Line ending issues: Configure Git to use LF endings

#### macOS Development
- Docker Desktop required
- Ensure sufficient resources allocated in Docker Desktop preferences

#### Linux Development
- Native Docker installation recommended
- May need to configure Docker socket permissions

### Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG
DEBUG=true

# For containerized development
docker-compose -f docker-compose.dev.yml exec orchestrator-dev bash
# Then run with debug
LOG_LEVEL=DEBUG uvicorn orchestrator.api.app:app --reload
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check Docker connectivity
docker ps

# Check container logs
make docker-dev-logs
```

## Advanced Configuration

### Custom Network Configuration

Create `docker-compose.override.yml`:
```yaml
version: '3.8'

networks:
  cto-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Resource Limits

In `docker-compose.override.yml`:
```yaml
version: '3.8'

services:
  orchestrator:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
```

### VSCode Remote Development

For the best IDE experience, use VSCode with Remote Containers:

1. Install "Remote - Containers" extension
2. Open project in VSCode
3. Click "Reopen in Container" when prompted
4. VSCode will use the development container

## Support

For issues and questions:

1. Check the [troubleshooting](#troubleshooting) section
2. Review the [DOCKER_DEV.md](DOCKER_DEV.md) for containerized development
3. Check [GitHub issues](https://github.com/joshcassell4/docorcpty/issues)
4. Open a new issue with:
   - System information (OS, Docker version)
   - Error messages
   - Steps to reproduce
   - Whether using local or containerized development