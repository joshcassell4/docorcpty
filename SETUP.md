# Container Terminal Orchestrator - Setup Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Development Setup](#development-setup)
4. [Docker Setup](#docker-setup)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Docker**: Version 20.10 or higher
- **Python**: Version 3.9 or higher
- **Node.js**: Version 18 or higher (for dashboard development)
- **Memory**: Minimum 4GB RAM
- **Storage**: At least 2GB free space

### Required Tools

```bash
# Check Docker version
docker --version

# Check Python version
python --version

# Check Node.js version (for development)
node --version

# Install UV package manager
pip install uv
```

## Installation Methods

### Method 1: Quick Start with Make

```bash
# Clone repository
git clone https://github.com/yourusername/docorcpty.git
cd docorcpty

# Run quick setup
make quickstart

# Start application
make docker-up
```

### Method 2: Manual Installation

```bash
# Clone repository
git clone https://github.com/yourusername/docorcpty.git
cd docorcpty

# Install Python dependencies with UV
uv pip sync --dev

# Install frontend dependencies
cd dashboard
npm install
cd ..

# Copy environment file
cp .env.sample .env

# Start services
docker-compose up -d
```

### Method 3: Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/docorcpty.git
cd docorcpty

# Complete development setup
make setup

# Initialize configuration
make init-config

# Start in development mode
make dev
```

## Development Setup

### Backend Development

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

### Frontend Development

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
# Add a new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update all dependencies
uv sync

# Create lock file
uv lock
```

## Docker Setup

### Building Images

```bash
# Build all images
make docker-build

# Build specific service
docker-compose build orchestrator
docker-compose build dashboard
```

### Running with Docker Compose

```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down

# Clean up
make clean-docker
```

### Docker Socket Access

The orchestrator needs access to the Docker socket. On Linux:

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again for changes to take effect
```

On macOS/Windows, Docker Desktop handles this automatically.

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

### Orchestrator Configuration

Main configuration is in `configs/orchestrator.json`:

```json
{
  "api_host": "0.0.0.0",
  "api_port": 8000,
  "docker_socket": "/var/run/docker.sock",
  "max_sessions": 50,
  "session_timeout": 3600,
  "log_level": "INFO"
}
```

## Troubleshooting

### Common Issues

#### Docker Socket Permission Denied

**Error**: `Permission denied while trying to connect to Docker daemon socket`

**Solution**:
```bash
# On Linux
sudo chmod 666 /var/run/docker.sock
# OR add user to docker group
sudo usermod -aG docker $USER
```

#### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port
lsof -i :8000
# Kill process or change port in .env
```

#### Container Creation Fails

**Error**: `Failed to create container`

**Possible causes**:
- Docker daemon not running
- Image not available locally
- Insufficient resources

**Solution**:
```bash
# Check Docker status
docker info

# Pull required images
docker pull python:3.9-slim
docker pull node:18-alpine
```

#### WebSocket Connection Failed

**Error**: `WebSocket connection failed`

**Solution**:
- Check firewall settings
- Ensure API is running
- Verify CORS settings in `.env`

### Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG
DEBUG=true

# Or via environment
LOG_LEVEL=DEBUG make run-dev
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check Docker connectivity
docker ps

# Test WebSocket
wscat -c ws://localhost:8000/ws/test
```

## Advanced Configuration

### Custom Network Configuration

```yaml
# docker-compose.override.yml
version: '3.8'

networks:
  cto_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Resource Limits

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  orchestrator:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
```

### SSL/TLS Configuration

For production, set up a reverse proxy with SSL:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Support

For issues and questions:

1. Check the [troubleshooting](#troubleshooting) section
2. Review [closed issues](https://github.com/yourusername/docorcpty/issues?q=is%3Aissue+is%3Aclosed)
3. Open a new issue with:
   - System information
   - Error messages
   - Steps to reproduce