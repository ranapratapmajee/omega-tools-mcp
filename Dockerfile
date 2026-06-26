# Use a lightweight, official Python image
FROM python:3.12-slim

# Install uv directly into the container from its official image distribution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working execution directory inside the container
WORKDIR /app

# 🛠️ Fix: Add README.md here so Hatchling can find it during sync!
COPY pyproject.toml uv.lock README.md ./

# Synchronize dependencies strictly matching your local lockfile setup
RUN uv sync --frozen --no-cache

# Copy your src module folder into the container workspace
COPY src/ ./src/

# Expose the internal container port 8000
EXPOSE 8000

# Fire up the engine running the web-based Server-Sent Events (SSE) protocol
CMD ["uv", "run", "src/omega_mcp/server.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]