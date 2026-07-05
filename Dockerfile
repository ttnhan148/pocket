# ── Stage 1: Build Frontend Static Bundle ───────────────────────────
FROM oven/bun:1.1.20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend config & dependencies
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile

# Copy frontend source code and compile Next.js static export
COPY frontend/ ./
RUN bun run build

# ── Stage 2: Create Monolithic Production Runner ──────────────────────
FROM python:3.12-slim AS runner
WORKDIR /app

# Install runtime system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Ensure multipart parsing is installed for form uploads
RUN pip install --no-cache-dir uvicorn python-multipart

# Copy backend app code and database configurations
COPY backend/app/ ./app/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini ./

# Copy compiled frontend static assets from Stage 1 into backend static serving directory
COPY --from=frontend-builder /app/frontend/out/ ./app/static/

# Create persistent storage folder for SQLite database files
RUN mkdir -p /app/data

EXPOSE 8000

ENV DATABASE_URL="sqlite+aiosqlite:////app/data/pocket.db"
ENV ENV_MODE="production"

# Start monolithic FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
