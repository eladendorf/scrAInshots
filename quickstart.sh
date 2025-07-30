#!/bin/bash

# ScrAInshots Quick Start Script

echo "🚀 ScrAInshots - AI-powered Screenshot Analyzer"
echo "=============================================="
echo ""

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed"
        return 1
    else
        echo "✅ $1 is installed"
        return 0
    fi
}

echo "Checking prerequisites..."
check_command "python3" || { echo "Please install Python 3.8+"; exit 1; }
check_command "node" || { echo "Please install Node.js 16+"; exit 1; }

# Install pnpm if not present
if ! check_command "pnpm"; then
    echo "Installing pnpm..."
    npm install -g pnpm
fi

# Install uv if not present
if ! check_command "uv"; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo ""
echo "Setting up project..."

# Install dependencies
echo "Installing Node.js dependencies..."
pnpm install

echo "Installing Python dependencies..."
uv sync || { echo "Failed to sync Python dependencies"; exit 1; }

# Check if on Mac for local LLM option
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "Detected macOS. Would you like to install local LLM support? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        uv sync --extra local
        echo "✅ Local LLM support installed"
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  make dev     # or pnpm dev"
echo ""
echo "For LM Studio mode:"
echo "  1. Start LM Studio on port 1234"
echo "  2. Load a model (e.g., google/gemma-3-12b)"
echo "  3. Run: make dev"
echo ""
echo "For local LLM mode (Mac only):"
echo "  1. Run: make dev"
echo "  2. Open Settings in the web UI"
echo "  3. Select 'Local MLX Runtime' and download a model"
echo ""
echo "Visit http://localhost:3000 to start!"