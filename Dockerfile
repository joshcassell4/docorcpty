FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv
RUN uv pip install --system -e .

# Copy application code
COPY orchestrator ./orchestrator
COPY configs ./configs

# Create workspace directory
RUN mkdir -p /workspace

# Expose API port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "orchestrator.api.app:app", "--host", "0.0.0.0", "--port", "8000"]