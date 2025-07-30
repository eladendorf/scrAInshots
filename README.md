# ScrAInshots - AI-Powered Screenshot Analyzer

An intelligent screenshot management system that uses AI to analyze, categorize, and search through your screenshots.

## Features

- **AI-Powered Analysis**: Automatically extract text, categorize content, and generate descriptions
- **Dual LLM Support**: Use either LM Studio API or run models locally with MLX
- **Smart Search**: Vector-based search to find screenshots by content
- **Rich Metadata**: Extract device type, dimensions, timestamps, and more
- **Interactive Viewer**: Next.js web app with filtering, word clouds, and markdown viewing
- **Cross-Platform**: Electron app for Mac, Windows, and Linux
- **Batch Processing**: Process multiple screenshots with progress tracking
- **AI Refinement**: Get additional context about companies, products, and topics

## 🔧 Build System

This project uses a modern build system with:

- **`uv`** - Fast Python package management with `pyproject.toml`
- **`pnpm`** - Unified commands for both Python and JavaScript
- **`make`** - Convenient shortcuts for common tasks

### Unified Commands

From the root directory, you can run:

```bash
# Setup and installation
pnpm setup          # Install everything
pnpm setup:python:local  # Add local LLM support (Mac)

# Development
pnpm dev           # Run both Python API and Next.js
pnpm dev:python    # Run Python API only
pnpm dev:next      # Run Next.js only

# Building
pnpm build         # Build for production
pnpm dist          # Build Electron distributables

# Testing and linting
pnpm test          # Run all tests
pnpm lint          # Check code style
pnpm lint:fix      # Fix code style issues

# Utilities
pnpm process       # Process screenshots
pnpm clean         # Clean generated files
```

### Makefile Shortcuts

For even quicker access:

```bash
make setup         # One-command setup
make setup-local   # Setup with local LLM support
make dev           # Start development
make electron      # Run Electron app
make dist          # Build distributables
make clean         # Clean everything
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- [pnpm](https://pnpm.io/) - Fast, disk space efficient package manager
- For local LLM: Apple Silicon Mac (M1/M2/M3)
- For API mode: LM Studio running on localhost:1234

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/scrainshots.git
cd scrainshots
```

2. Install pnpm (if not already installed):
```bash
npm install -g pnpm
```

3. Quick setup options:

**Option A: Interactive setup (Recommended)**
```bash
./quickstart.sh
```

**Option B: Using make**
```bash
make setup
# Or for local LLM support on Mac:
make setup-local
```

**Option C: Using pnpm directly**
```bash
pnpm setup
# For local LLM support:
pnpm setup:python:local
```

### Running the Application

#### Quick Start (All-in-One)

```bash
# Start everything with one command:
make dev
# Or:
pnpm dev
```

This will start both the Python API server and Next.js frontend.

#### Running Backend and Frontend Separately

```bash
# Run backend (Python API server on port 8000):
pnpm dev:python
# Or directly:
uv run python api_flask_server.py

# Run browser/frontend (Next.js on port 3000):
pnpm dev:next
# Or:
cd screenshot-viewer && pnpm dev
```

#### Option 1: LM Studio Mode (Recommended)

1. Download and run [LM Studio](https://lmstudio.ai/)
2. Load a model (e.g., `google/gemma-3-12b`)
3. Start the server on port 1234
4. Run: `make dev`

#### Option 2: Local LLM Mode (Mac only)

1. Setup: `make setup-local`
2. Run: `make dev`
3. Open Settings in the web UI and:
   - Select "Local MLX Runtime"
   - Download a model (gemma-2b recommended for starters)

#### Option 3: Electron App

```bash
# Development
make electron
# Or:
pnpm electron:dev

# Build distributable
make dist
# Or:
pnpm dist
```

## Usage

1. **Configure Screenshots Folder**: 
   - Default: `~/Desktop/screenshots` (Mac)
   - Or use File → Select Screenshots Folder

2. **Process Screenshots**:
   - Click "Process Screenshots" to analyze unprocessed images
   - Progress bar shows real-time status

3. **Search and Filter**:
   - Use the search bar to find screenshots by content
   - Filter by date range
   - View word cloud of all content

4. **View and Refine**:
   - Click any screenshot to view full analysis
   - Use "Refine with AI" to get additional context
   - Open original screenshot with "View Original"

## Architecture

```
scrainshots/
├── screenshot_processor.py      # Core processing logic
├── database_manager.py         # ChromaDB vector storage
├── local_llm.py               # MLX local model support
├── batch_processor.py         # Batch processing with progress
├── api_server.py             # Python API server (port 8000)
├── pyproject.toml            # Python dependencies (uv)
├── package.json              # Root orchestration (pnpm)
├── Makefile                  # Convenient shortcuts
├── quickstart.sh             # Interactive setup script
└── screenshot-viewer/        # Next.js + Electron app
    ├── src/app/             # Next.js pages and API
    ├── src/components/      # React components
    ├── electron.js          # Electron main process
    └── package.json         # Frontend dependencies
```

### System Flow

1. **Python API Server** (`api_server.py`) runs on port 8000
2. **Next.js Frontend** runs on port 3000 and communicates with Python API
3. **Screenshot Processor** uses either LM Studio API or local MLX models
4. **ChromaDB** stores analyzed content for vector search
5. **Electron Wrapper** packages everything as a desktop app

## Supported Models

### Local Models (MLX)
- **gemma-2b**: Lightweight, 1.5GB, good for basic tasks
- **phi-3-mini**: Small but capable, 2.4GB
- **mistral-7b**: Powerful, 4.1GB, requires 16GB+ RAM

### LM Studio
- Any model supported by LM Studio
- Recommended: gemma-3-12b, llama-3, mistral

## Configuration

Settings are stored in `~/.scrainshots/config.json`:

```json
{
  "runtime": "lmstudio",
  "local_model": "gemma-2b",
  "lmstudio_url": "http://localhost:1234/v1",
  "lmstudio_model": "google/gemma-3-12b"
}
```

## Development

### Project Structure

The project uses a monorepo structure with:
- **Root**: Python backend and build orchestration
- **screenshot-viewer/**: Next.js frontend and Electron app

### Available Commands

All commands can be run from the root directory:

```bash
# Development
make dev          # Start all services
make process      # Process screenshots
make test         # Run tests
make lint         # Check code style
make lint-fix     # Fix code style
make clean        # Clean generated files

# Or using pnpm:
pnpm dev          # Start all services
pnpm process      # Process screenshots
pnpm test         # Run tests
pnpm lint         # Check code style
pnpm lint:fix     # Fix code style
pnpm clean        # Clean generated files
```

### Adding New Models

Edit `local_llm.py` to add support for new MLX models:

```python
self.supported_models["new-model"] = {
    "hf_repo": "org/model-name",
    "mlx_repo": "mlx-community/model-name-4bit",
    "size": "X.XGB",
    "description": "Model description"
}
```

### Custom Prompts

Modify the analysis prompt in `screenshot_processor.py`:

```python
prompt = f"""Your custom prompt here..."""
```

## Troubleshooting

### MLX Installation Issues
- Ensure you have an Apple Silicon Mac
- Update to latest macOS
- Try: `uv pip install --upgrade mlx mlx-lm`
- Or reinstall: `uv sync --extra local --reinstall`

### LM Studio Connection
- Check LM Studio is running on port 1234
- Verify model is loaded
- Test: `curl http://localhost:1234/v1/models`

### Database Issues
- Delete `./screenshot_db` to reset
- Check disk space for ChromaDB

## License

MIT License - see LICENSE file

## Contributing

Pull requests welcome! Please see CONTRIBUTING.md for guidelines.