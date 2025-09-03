#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "?? Starting project setup..."

# === 1. Update and install system dependencies ===
echo "?? Installing system dependencies..."
sudo apt-get update && sudo apt-get install -y \
    python3-pip \
    python3-venv \
    ffmpeg \
    openssl \
    net-tools \
    curl \
    build-essential \
    lsof # For port checking

# === 2. Create Python virtual environment ===
echo "?? Creating Python virtual environment..."
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "? Virtual environment created."
fi
source venv/bin/activate

# === 3. Install Python packages ===
echo "?? Installing Python dependencies (Torch + CUDA 12.6)..."
pip install --upgrade pip
pip install torch==2.6.0+cu126 torchvision==0.21.0+cu126 torchaudio==2.6.0+cu126 --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements.txt

# === 4. Create required directories ===
echo "?? Creating project directories..."
mkdir -p daily_standup/audio \
         daily_standup/temp \
         daily_standup/reports \
         weekly_interview/audio \
         weekly_interview/temp \
         weekly_interview/reports \
         static \
         certs \
         env \
         TMPS/certs

# === 5. Install Node.js dependencies for TMPS frontend ===
echo "?? Installing Node.js dependencies in TMPS..."
(cd TMPS && npm install)

# === 6. Generate self-signed SSL certificates ===
echo "?? Checking for and generating self-signed SSL certificates..."

generate_certs() {
  local cert_dir="$1"
  if [ ! -f "$cert_dir/cert.pem" ] || [ ! -f "$cert_dir/key.pem" ]; then
    echo "?? Generating certificates in $cert_dir..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$cert_dir/key.pem" \
      -out "$cert_dir/cert.pem" \
      -subj "/C=IN/ST=TS/L=Hyderabad/O=Lanciere/OU=Dev/CN=localhost"
    echo "? Certificates created in $cert_dir"
  else
    echo "?? Certificates already exist in $cert_dir. Skipping."
  fi
}

generate_certs "./certs"
generate_certs "./TMPS/certs"

# === 7. Check if ports 8090 and 5174 are available ===
echo "?? Checking ports 8090 and 5174..."
for port in 8090 5174; do
  if lsof -i:$port >/dev/null 2>&1; then
    echo "?? Port $port is already in use."
  else
    echo "? Port $port is free."
  fi
done

# === 8. Create .env template for OpenAI & GROQ ===
ENV_PATH="./env/.env"
if [ ! -f "$ENV_PATH" ]; then
  echo "?? Creating .env template for API keys..."
  cat > "$ENV_PATH" <<EOL
# ?? Add your API keys here

OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key
EOL
  echo "? .env file created at $ENV_PATH ? Please edit it and add your real keys."
else
  echo "?? .env file already exists. Skipping creation."
fi

echo "?? Setup completed successfully!"
