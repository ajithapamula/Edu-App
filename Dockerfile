# === Stage 1: Base image with CUDA and Python ===
# Use NVIDIA's official CUDA image to support GPU-accelerated PyTorch.
FROM nvidia/cuda:12.6.0-base-ubuntu22.04 AS base

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install Python, pip, and other system dependencies from setup.sh
# Added git as it's required by GitPython
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    ffmpeg \
    openssl \
    net-tools \
    curl \
    build-essential \
    lsof \
    git \
    && rm -rf /var/lib/apt/lists/*

# Make python3.11 the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1


# === Stage 2: Python dependency builder ===
FROM base AS python-builder

# Create and activate a virtual environment for clean dependency management
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements file and install dependencies
# This leverages Docker's layer caching. This step only re-runs if requirements.txt changes.
COPY requirements.txt .
RUN pip install torch==2.6.0+cu126 torchvision==0.21.0+cu126 torchaudio==2.6.0+cu126 --index-url https://download.pytorch.org/whl/cu126
RUN pip install -r requirements.txt


# === Stage 3: Node.js frontend builder ===
FROM node:20-slim AS frontend-builder

WORKDIR /app/TMPS

# Copy package files and install dependencies
COPY TMPS/package.json TMPS/package-lock.json* ./
RUN npm install

# Copy the rest of the frontend source code and build for production
COPY TMPS/ ./
RUN npm run build


# === Stage 4: Final production image ===
FROM base AS final

WORKDIR /app

# Create a non-root user and group for better security
RUN groupadd --system appgroup && useradd --system --gid appgroup --create-home appuser

# Copy the virtual environment with installed Python packages
COPY --from=python-builder /opt/venv /opt/venv

# Copy the application code. A .dockerignore file is crucial here.
COPY . .

# Copy the built frontend assets from the frontend-builder stage
# Assuming the backend serves these files from a 'static' directory.
COPY --from=frontend-builder /app/TMPS/build ./static/tmps_frontend

# Set ownership for the entire app directory to the non-root user
RUN chown -R appuser:appgroup /app /opt/venv

# Switch to the non-root user
USER appuser

# Add venv to the PATH for the appuser
ENV PATH="/opt/venv/bin:$PATH"

# Create required directories and generate SSL certificates, mimicking setup.sh safely
RUN mkdir -p daily_standup/audio daily_standup/temp daily_standup/reports weekly_interview/audio weekly_interview/temp weekly_interview/reports static certs TMPS/certs && \
    if [ ! -f "./certs/cert.pem" ]; then openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "./certs/key.pem" -out "./certs/cert.pem" -subj "/C=IN/ST=TS/L=Hyderabad/O=Lanciere/OU=Dev/CN=localhost"; fi && \
    if [ ! -f "./TMPS/certs/cert.pem" ]; then openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "./TMPS/certs/key.pem" -out "./TMPS/certs/cert.pem" -subj "/C=IN/ST=TS/L=Hyderabad/O=Lanciere/OU=Dev/CN=localhost"; fi

# Expose the ports the application will run on
EXPOSE 8070
EXPOSE 5179

# Command to run the application.
# Assumes your FastAPI app instance is named 'app' in a file named 'main.py'.
# Adjust 'main:app' as necessary.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8070", "--ssl-keyfile", "./certs/key.pem", "--ssl-certfile", "./certs/cert.pem"]