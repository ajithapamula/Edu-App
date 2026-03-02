#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "🚀 Starting project setup..."

# === 1. Update and install system dependencies ===
echo "📦 Installing system dependencies..."
sudo apt-get update && sudo apt-get install -y \
    python3-pip \
    python3-venv \
    ffmpeg \
    openssl \
    net-tools \
    curl \
    build-essential \
    lsof # For port checking

# === 2. Install Docker & Piston (Code Execution Engine) ===
echo "🐳 Setting up Docker..."
if ! command -v docker &> /dev/null; then
    echo "📥 Installing Docker..."
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    echo "✅ Docker installed."
else
    echo "✅ Docker already installed: $(docker --version)"
fi

echo "⚡ Setting up Piston (Code Execution Engine)..."
if ! sudo docker ps -a --format '{{.Names}}' | grep -q '^piston$'; then
    echo "📥 Pulling and starting Piston..."
    sudo docker run -d \
        --name piston \
        --restart always \
        -p 2000:2000 \
        ghcr.io/engineer-man/piston

    echo "⏳ Waiting 30 seconds for Piston to initialize..."
    sleep 30

    # Install language runtimes
    echo "📦 Installing Python runtime..."
    sudo docker exec piston piston ppman install python=3.10.0

    echo "📦 Installing Node.js runtime..."
    sudo docker exec piston piston ppman install node=18.15.0

    echo "📦 Installing Java runtime..."
    sudo docker exec piston piston ppman install java=15.0.2

    echo "📦 Installing C/C++ runtime..."
    sudo docker exec piston piston ppman install gcc=10.2.0

    echo "📦 Installing TypeScript runtime..."
    sudo docker exec piston piston ppman install typescript=5.0.3

    echo "✅ Piston ready with Python, Node.js, Java, C/C++, TypeScript"
else
    # Make sure Piston is running
    if ! sudo docker ps --format '{{.Names}}' | grep -q '^piston$'; then
        echo "🔄 Piston exists but stopped. Starting..."
        sudo docker start piston
        sleep 10
    fi
    echo "✅ Piston already running."
fi

# Verify Piston is working
echo "🧪 Testing Piston..."
PISTON_TEST=$(curl -s -X POST http://localhost:2000/api/v2/execute \
    -H "Content-Type: application/json" \
    -d '{"language":"python","version":"3.10.0","files":[{"content":"print(3+5)"}]}' 2>/dev/null || echo "FAILED")

if echo "$PISTON_TEST" | grep -q '"stdout":"8'; then
    echo "✅ Piston test passed! Code execution working."
else
    echo "⚠️ Piston test failed. You may need to wait and retry."
    echo "   Response: $PISTON_TEST"
fi

# === 3. Create Python virtual environment ===
echo "🐍 Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
fi
source venv/bin/activate

# === 4. Install Python packages ===
echo "📦 Installing Python dependencies (Torch + CUDA 12.6)..."
pip install --upgrade pip
pip install torch==2.6.0+cu126 torchvision==0.21.0+cu126 torchaudio==2.6.0+cu126 --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements.txt

# Install httpx for Piston API calls from backend
pip install httpx
echo "✅ httpx installed for code execution service."

# === 5. Create required directories ===
echo "📁 Creating project directories..."
mkdir -p daily_standup/audio \
         daily_standup/temp \
         daily_standup/reports \
         weekly_interview/audio \
         weekly_interview/temp \
         weekly_interview/reports \
         static \
         certs \
         env

# === 6. Generate self-signed SSL certificates ===
echo "🔐 Checking for and generating self-signed SSL certificates..."
generate_certs() {
    local cert_dir="$1"
    if [ ! -f "$cert_dir/cert.pem" ] || [ ! -f "$cert_dir/key.pem" ]; then
        echo "🔑 Generating certificates in $cert_dir..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$cert_dir/key.pem" \
            -out "$cert_dir/cert.pem" \
            -subj "/C=IN/ST=TS/L=Hyderabad/O=Lanciere/OU=Dev/CN=localhost"
        echo "✅ Certificates created in $cert_dir"
    else
        echo "✅ Certificates already exist in $cert_dir. Skipping."
    fi
}
generate_certs "./certs"

# === 7. Check if ports are available ===
echo "🔍 Checking ports 8090, 5174, and 2000..."
for port in 8090 5174 2000; do
    if lsof -i:$port >/dev/null 2>&1; then
        echo "⚠️ Port $port is already in use."
    else
        echo "✅ Port $port is free."
    fi
done

# === 8. Create .env template ===
ENV_PATH="./env/.env"
if [ ! -f "$ENV_PATH" ]; then
    echo "📝 Creating .env template for API keys..."
    cat > "$ENV_PATH" <<EOL
# 🔑 Add your API keys here
OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key

# ⚡ Piston Code Execution (auto-configured by setup)
PISTON_API_URL=http://localhost:2000
EOL
    echo "✅ .env file created at $ENV_PATH → Please edit it and add your real keys."
else
    # Add PISTON_API_URL if missing
    if ! grep -q "PISTON_API_URL" "$ENV_PATH"; then
        echo "" >> "$ENV_PATH"
        echo "# ⚡ Piston Code Execution (auto-configured by setup)" >> "$ENV_PATH"
        echo "PISTON_API_URL=http://192.168.48.201:2000" >> "$ENV_PATH"
        echo "✅ Added PISTON_API_URL to existing .env"
    fi
    echo "✅ .env file already exists."
fi
