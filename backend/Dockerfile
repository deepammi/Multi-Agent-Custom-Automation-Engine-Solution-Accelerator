# Multi-stage Dockerfile for MACAE Backend with MCP SDK support

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for MCP SDK
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies including MCP SDK
RUN pip install --no-cache-dir -r requirements.txt

# Verify MCP SDK installation
RUN python -c "import mcp; print(f'MCP SDK version: {mcp.__version__}')"

# Copy application code
COPY . .

# Copy MCP server implementations
COPY ../src/mcp_server/ ./src/mcp_server/

# Set up proper permissions for MCP server scripts
RUN chmod +x src/mcp_server/*.py

# Create directories for configuration and logs
RUN mkdir -p config logs

# Copy configuration files
COPY config/ ./config/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]