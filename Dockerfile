# filepath: ./Dockerfile
FROM python:3.11-slim-bookworm

# Install uv directly from the official optimized image distribution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set production execution workspace directory
WORKDIR /app

# Enable bytecode compilation for rapid application startup speed
ENV UV_COMPILE_BYTECODE=1
# Stop python from writing ephemeral .pyc clutter onto container disk layers
ENV PYTHONDONTWRITEBYTECODE=1
# Force stream tracing logs to unbuffered mode to instantly pipe stderr to Docker metrics
ENV PYTHONUNBUFFERED=1

# Copy project package configurations first to preserve cache layers optimally
COPY pyproject.toml uv.lock ./

# Synchronize virtual env configurations globally directly into base system framework layers
RUN uv pip install --system -r pyproject.toml

# Copy the decoupled core modules and tool structures into active container matrix
COPY src/ /app/src/

# Expose internal runtime container networking port
EXPOSE 8000

# Set baseline infrastructure defaults (can be modified inside docker-compose)
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV PYTHONPATH=/app/src

# Invoke the application layer entry point via the standard python runtime engine
CMD ["python", "src/omega_mcp/server.py"]