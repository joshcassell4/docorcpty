# Container Terminal Orchestrator (CTO)

A Python-based container orchestration platform that enables seamless management, interaction, and automation of containerized terminal applications including development tools, games, utilities, and commands.

## Features

- **Container Management**: Create, start, stop, and remove Docker containers
- **Interactive Terminal Sessions**: Real-time terminal access via WebSocket
- **Web Dashboard**: Modern React-based UI for container and session management
- **Automation Support**: Script execution and terminal automation with pexpect
- **Resource Monitoring**: Real-time system and container resource tracking
- **Multi-Session Support**: Handle up to 50 concurrent terminal sessions
- **Pre-configured Templates**: Ready-to-use container configurations

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Web Dashboard  │────▶│  FastAPI     │────▶│   Docker    │
│    (React)      │     │  REST API    │     │  Containers │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                      │
         │                      │
         └──── WebSocket ──────┘
              (Terminal I/O)
```

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Python 3.9+
- Node.js 18+ (for dashboard development)
- UV package manager (`pip install uv`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/docorcpty.git
cd docorcpty
```

2. Set up the development environment:
```bash
make setup
```

3. Initialize configuration:
```bash
make init-config
```

4. Start the application:
```bash
# Development mode
make dev

# Docker mode
make docker-up
```

The API will be available at http://localhost:8000 and the dashboard at http://localhost:3000.

## Usage

### Creating a Container

1. Open the dashboard at http://localhost:3000
2. Click "Create Container"
3. Select a template (Python Dev, Node.js Dev, etc.)
4. Click "Create"

### Starting a Terminal Session

1. Find your running container in the grid
2. Click the terminal icon
3. A new terminal session will open in the dashboard

### Using the API

```python
import requests

# Create a container
response = requests.post('http://localhost:8000/api/containers', 
                        json={'name': 'python-dev'})
container_id = response.json()['container_id']

# Create a session
response = requests.post('http://localhost:8000/api/sessions',
                        json={'container_id': container_id})
session_id = response.json()['session_id']
```

## Configuration

### Container Templates

Pre-configured containers are available in `configs/containers/`:

- **python-dev.json**: Python 3.9 development environment
- **node-dev.json**: Node.js 18 development environment
- **ascii-games.json**: Ubuntu with ASCII games
- **system-monitor.json**: Alpine Linux for system monitoring

### Environment Variables

Copy `.env.sample` to `.env` and configure:

```env
API_PORT=8000
MAX_CONCURRENT_SESSIONS=50
CONTAINER_MEMORY_LIMIT=512m
SESSION_TIMEOUT_SECONDS=3600
```

## Development

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# With coverage
make test-coverage
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check
```

### Building for Production

```bash
# Build Docker images
make docker-build

# Build frontend
make frontend-build
```

## API Documentation

### Endpoints

#### Containers
- `GET /api/containers` - List containers
- `POST /api/containers` - Create container
- `GET /api/containers/{id}` - Get container details
- `POST /api/containers/{id}/action` - Perform action (start/stop/remove)
- `GET /api/containers/{id}/stats` - Get resource stats
- `GET /api/containers/{id}/logs` - Get container logs

#### Sessions
- `GET /api/sessions` - List sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session details
- `DELETE /api/sessions/{id}` - Close session
- `WebSocket /ws/{session_id}` - Terminal I/O

#### Automation
- `POST /api/automation/execute` - Execute script
- `GET /api/automation/templates` - List templates
- `POST /api/automation/templates/{name}/execute` - Execute template

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with FastAPI, Docker, React, and xterm.js
- Uses dockerpty for pseudo-terminal allocation
- Terminal automation powered by pexpect