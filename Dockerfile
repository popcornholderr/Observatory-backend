# ---- Stage 1: build the Rust backend ----
FROM rust:latest AS builder

WORKDIR /app/backend
COPY backend/Cargo.toml backend/Cargo.lock* ./
# Pre-fetch deps for better layer caching (ok if this fails on first run, cargo build below covers it)
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release || true

COPY backend/src ./src
RUN cargo build --release

# ---- Stage 2: runtime image with Python + the compiled binary ----
FROM python:3.11-slim

# Install Python deps for the analysis pipeline
WORKDIR /app/python-analysis
COPY python-analysis/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY python-analysis/ .

# Bring in the compiled Rust binary
WORKDIR /app/backend
COPY --from=builder /app/backend/target/release/backend ./backend

# Data dirs the Rust app writes to (uploads + results), created up front
RUN mkdir -p /app/data/uploads /app/data/results

# Env vars matching the Rust code's relative-path expectations
# (CWD is /app/backend, so "../python-analysis" and "../data/..." resolve correctly)
ENV PYTHON_BIN=python3
ENV PYTHON_SCRIPT_DIR=../python-analysis
ENV UPLOADS_DIR=../data/uploads
ENV RESULTS_DIR=../data/results

EXPOSE 8000
CMD ["./backend"]
