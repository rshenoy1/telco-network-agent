# ==========================================
# STAGE 1: Build & Dependency Gathering
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies needed for compiling certain python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker caching layers
COPY requirements.txt .

# Install dependencies into a localized wheel or user directory
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# STAGE 2: Final Slim Runtime Environment
# ==========================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Ensure the installed user packages are accessible in the system PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy your core application code into the image container
COPY main.py .

# Expose port 8000 for your combined FastAPI & Gradio interface
EXPOSE 8000

# Run Uvicorn directly through Python using optimal production worker settings
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]