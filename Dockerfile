FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    intel-opencl-icd \
    tzdata \
    fonts-dejavu-core \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set environment variables
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Sync dependencies (frozen ensures we use uv.lock)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Ensure data directory exists
RUN mkdir -p /app/data

# Default environment variables (can be overridden by Coolify)
ENV DATABASE_PATH=/app/data/map.db
ENV AUDIO_FOLDER=/app/data/audio
ENV SCREENSHOTS_DIR=/app/data/screenshots

# Command to run the bot
CMD ["uv", "run", "python", "bot.py"]
