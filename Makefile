.PHONY: help setup dev build clean test lint install-uv

# Default target
help:
	@echo "ScrAInshots - AI-powered Screenshot Analyzer"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup       - Install all dependencies (uv + pnpm)"
	@echo "  make setup-local - Setup with local LLM support"
	@echo "  make dev         - Run development servers"
	@echo "  make build       - Build production version"
	@echo "  make electron    - Run Electron app in dev mode"
	@echo "  make dist        - Build Electron distributables"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run linters"
	@echo "  make clean       - Clean all generated files"

# Check if uv is installed
check-uv:
	@command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)

# Check if pnpm is installed
check-pnpm:
	@command -v pnpm >/dev/null 2>&1 || (echo "Error: pnpm is not installed. Please install it first: npm install -g pnpm" && exit 1)

# Setup everything
setup: check-uv check-pnpm
	@echo "Setting up ScrAInshots..."
	pnpm install
	uv sync
	@echo "✅ Setup complete!"

# Setup with local LLM support
setup-local: setup
	@echo "Installing local LLM dependencies..."
	uv sync --extra local
	@echo "✅ Local LLM setup complete!"

# Development mode
dev: check-uv check-pnpm
	@echo "Starting development servers..."
	pnpm dev

# Build for production
build: check-uv check-pnpm
	@echo "Building for production..."
	pnpm build

# Run Electron in development
electron: check-uv check-pnpm
	@echo "Starting Electron app..."
	pnpm electron:dev

# Build Electron distributables
dist: build
	@echo "Building Electron distributables..."
	pnpm dist

# Run tests
test: check-uv check-pnpm
	@echo "Running tests..."
	pnpm test

# Run linters
lint: check-uv check-pnpm
	@echo "Running linters..."
	pnpm lint

# Fix linting issues
lint-fix: check-uv check-pnpm
	@echo "Fixing linting issues..."
	pnpm lint:fix

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	pnpm clean
	@echo "✅ Clean complete!"

# Process screenshots
process:
	@echo "Processing screenshots..."
	pnpm process

# Quick start guide
quickstart: setup
	@echo ""
	@echo "🚀 Quick Start Guide:"
	@echo ""
	@echo "1. For LM Studio mode:"
	@echo "   - Start LM Studio on port 1234"
	@echo "   - Run: make dev"
	@echo ""
	@echo "2. For local LLM mode (Mac only):"
	@echo "   - Run: make setup-local"
	@echo "   - Run: make dev"
	@echo "   - Open Settings to download models"
	@echo ""
	@echo "3. For Electron app:"
	@echo "   - Run: make electron"
	@echo ""
	@echo "Visit http://localhost:3000 to start!"