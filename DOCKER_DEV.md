# Containerized Development Environment

This guide explains how to use the containerized development environment for the Container Terminal Orchestrator project.

## Why Use Containerized Development?

Developing inside Docker containers provides several benefits:
- **Cross-platform compatibility**: No Windows-specific issues (like missing `fcntl` module)
- **Consistent environment**: Same setup across all developers
- **Isolated dependencies**: No conflicts with your system Python or Node.js
- **Easy cleanup**: Just remove containers when done

## Quick Start

1. **Start the development environment:**
   ```bash
   make docker-dev
   ```
   This will build and start both the orchestrator and dashboard in development mode with hot-reloading.

2. **Access the application:**
   - API: http://localhost:8000
   - Dashboard: http://localhost:3000
   - API Docs: http://localhost:8000/docs

3. **View logs:**
   ```bash
   make docker-dev-logs
   ```

## Development Workflow

### Making Code Changes

1. Edit files on your host machine using your preferred editor
2. Changes are automatically synced to the containers via volume mounts
3. The orchestrator will auto-reload when Python files change
4. The dashboard will hot-reload when React files change

### Running Commands in the Container

To run commands inside the orchestrator container:
```bash
make docker-dev-shell
```

Then you can run commands like:
```bash
# Run tests
pytest

# Install new dependencies
uv pip install package-name

# Run linting
ruff check .

# Run type checking
mypy orchestrator
```

### Managing the Environment

```bash
# Start containers in background
make docker-dev-up

# Stop containers
make docker-dev-down

# Restart containers
make docker-dev-restart

# Remove everything (containers, volumes, etc.)
make docker-dev-clean
```

## Architecture

The development environment consists of:

1. **orchestrator-dev**: Python backend with FastAPI
   - Mounts `./orchestrator` for code changes
   - Mounts Docker socket for container management
   - Includes development tools (ipython, ipdb, vim)

2. **dashboard-dev**: React frontend
   - Mounts `./dashboard/src` and `./dashboard/public`
   - Runs with hot-reloading enabled
   - Proxies API requests to orchestrator

3. **postgres-dev**: PostgreSQL database (optional)
4. **redis-dev**: Redis cache (optional)

## Troubleshooting

### Permission Issues
If you encounter permission issues with the Docker socket:
```bash
# On Linux/Mac
sudo chmod 666 /var/run/docker.sock

# On Windows (Docker Desktop)
# The socket should work automatically
```

### Port Conflicts
If ports 8000 or 3000 are already in use:
1. Stop the conflicting service, or
2. Modify the ports in `docker-compose.dev.yml`

### Container Not Starting
Check the logs:
```bash
make docker-dev-logs
```

### Clean Start
If you need a completely fresh start:
```bash
make docker-dev-clean
make docker-dev-build
make docker-dev
```

## Advanced Usage

### Installing New Dependencies

1. Enter the container:
   ```bash
   make docker-dev-shell
   ```

2. Install the dependency:
   ```bash
   uv pip install new-package
   ```

3. Update pyproject.toml on your host machine

4. Rebuild the image:
   ```bash
   make docker-dev-build
   ```

### Debugging

The development containers include debugging tools:

1. **Python debugging with ipdb:**
   ```python
   import ipdb; ipdb.set_trace()
   ```

2. **Interactive Python shell:**
   ```bash
   make docker-dev-shell
   ipython
   ```

### Running Tests

```bash
# Run all tests in container
docker-compose -f docker-compose.dev.yml exec orchestrator-dev pytest

# Run with coverage
docker-compose -f docker-compose.dev.yml exec orchestrator-dev pytest --cov=orchestrator
```

## Benefits Over Local Development

1. **No Windows Issues**: All Linux-specific dependencies work perfectly
2. **Clean System**: Your host system stays clean
3. **Team Consistency**: Everyone has the same environment
4. **Easy Onboarding**: New developers just run one command
5. **Production-Like**: Closer to how the app runs in production

## Next Steps

- Customize the environment by modifying `docker-compose.dev.yml`
- Add more development tools to `Dockerfile.dev`
- Set up VS Code Remote Containers for IDE integration