# --- Builder Stage ---
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Install build tools needed for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1

# Install dependencies into a portable directory
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# --- Final Runner Stage ---
FROM python:3.13-slim-bookworm

# Install ONLY runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    intel-opencl-icd \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Ensure data directory exists
RUN mkdir -p /app/data

# Copy the uv binary from the builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Ensure paths match your config
ENV DATABASE_PATH=/app/data/map.db
ENV AUDIO_FOLDER=/app/data/audio
ENV SCREENSHOTS_DIR=/app/data/screenshots

CMD ["uv", "run", "python", "bot.py"]
