# Makefile for Invoice Generator
# This Makefile provides convenient commands for development, testing, and deployment

.PHONY: help install install-uv setup test demo clean run lint format check-env show-config

# Default target
help:
	@echo "Invoice Generator - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "Environment Setup:"
	@echo "  install-uv    Install UV package manager"
	@echo "  install       Install dependencies using UV"
	@echo "  setup         Complete project setup (install UV + deps + config)"
	@echo ""
	@echo "Development:"
	@echo "  run           Run the interactive invoice generator"
	@echo "  demo          Run demo with sample invoices"
	@echo "  samples       Generate sample invoices for different scenarios"
	@echo "  test          Run PDF generation tests"
	@echo "  lint          Run code linting with ruff"
	@echo "  format        Format code with ruff"
	@echo ""
	@echo "Configuration:"
	@echo "  check-env     Check environment configuration"
	@echo "  show-config   Show current configuration values"
	@echo "  init-env      Create .env file from template"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean         Clean up generated files and cache"
	@echo "  clean-all     Clean everything including virtual environment"
	@echo "  update        Update dependencies to latest versions"
	@echo "  relock        Regenerate lock file for current platform"
	@echo "  platform-info Show platform and dependency information"
	@echo ""
	@echo "Packaging:"
	@echo "  build         Build the package"
	@echo "  install-dev   Install in development mode"
	@echo ""

# Check if UV is installed
check-uv:
	@command -v uv >/dev/null 2>&1 || { echo "UV not found. Run 'make install-uv' first."; exit 1; }

# Install UV package manager
install-uv:
	@echo "📦 Installing UV package manager..."
	@if command -v uv >/dev/null 2>&1; then \
		echo "✅ UV is already installed"; \
		uv --version; \
	else \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "✅ UV installed successfully"; \
	fi

# Install dependencies using UV
install: check-uv
	@echo "📦 Installing dependencies with UV..."
	uv sync
	@echo "✅ Dependencies installed successfully"

# Complete project setup
setup: install-uv install init-env
	@echo "🎉 Project setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env file with your company details"
	@echo "  2. Set up Microsoft Graph API (see README.md)"
	@echo "  3. Run 'make demo' to test PDF generation"
	@echo "  4. Run 'make run' for the full application"

# Create .env file from template
init-env:
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from template..."; \
		cp .env.example .env; \
		echo "✅ .env file created. Please edit it with your details."; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

# Run the main application
run: check-uv
	@echo "🚀 Starting Invoice Generator..."
	uv run python main.py

# Run demo with sample invoices
demo: check-uv
	@echo "🎭 Running invoice generation demo..."
	uv run python demo.py

# Run tests
test: check-uv
	@echo "🧪 Running PDF generation tests..."
	uv run python test_pdf.py

# Install development dependencies and tools
install-dev: check-uv
	@echo "📦 Installing development dependencies..."
	uv add --dev ruff mypy pytest
	@echo "✅ Development dependencies installed"

# Run code linting
lint: check-uv
	@echo "🔍 Running code linting..."
	@if uv run ruff check . 2>/dev/null; then \
		echo "✅ Linting passed"; \
	else \
		echo "⚠️  Installing ruff first..."; \
		uv add --dev ruff; \
		uv run ruff check .; \
	fi

# Format code
format: check-uv
	@echo "✨ Formatting code..."
	@if uv run ruff format . 2>/dev/null; then \
		echo "✅ Code formatted"; \
	else \
		echo "⚠️  Installing ruff first..."; \
		uv add --dev ruff; \
		uv run ruff format .; \
	fi

# Type checking
typecheck: check-uv
	@echo "🔍 Running type checking..."
	@if uv run mypy . 2>/dev/null; then \
		echo "✅ Type checking passed"; \
	else \
		echo "⚠️  Installing mypy first..."; \
		uv add --dev mypy; \
		uv run mypy --install-types --non-interactive .; \
	fi

# Check environment configuration
check-env:
	@echo "🔧 Checking environment configuration..."
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		echo "📋 Configuration summary:"; \
		grep -E "^COMPANY_NAME=|^HOURLY_RATE=|^MICROSOFT_CLIENT_ID=" .env 2>/dev/null || echo "⚠️  Some configuration values may be missing"; \
	else \
		echo "❌ .env file not found. Run 'make init-env' first"; \
	fi

# Show current configuration
show-config: check-uv
	@echo "📋 Current configuration:"
	@uv run python -c "import config; print(f'Company: {config.COMPANY_NAME}'); print(f'Hourly Rate: {config.CURRENCY_SYMBOL}{config.HOURLY_RATE}'); print(f'Hours/Day: {config.HOURS_PER_DAY}'); print(f'Email: {config.COMPANY_EMAIL}')" 2>/dev/null || echo "⚠️  Could not load configuration. Check .env file."

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf invoices/*.pdf
	@echo "✅ Cleanup complete"

# Clean everything including virtual environment
clean-all: clean
	@echo "🧹 Cleaning virtual environment..."
	rm -rf .venv/
	@echo "✅ Complete cleanup finished"

# Update dependencies
update: check-uv
	@echo "📦 Updating dependencies..."
	uv lock --upgrade
	uv sync
	@echo "✅ Dependencies updated"

# Regenerate lock file optimized for current platform
relock: check-uv
	@echo "� Regenerating lock file..."
	rm -f uv.lock
	uv lock --resolution=highest
	@echo "✅ Lock file regenerated for current platform"

# Show platform information
platform-info:
	@echo "📊 Platform Information"
	@echo "======================"
	@echo "OS: $(shell uname -s)"
	@echo "Architecture: $(shell uname -m)"
	@echo "Python Platform: $(shell python -c 'import sysconfig; print(sysconfig.get_platform())')"
	@echo "Packages in lock file: $(shell grep -c "^\\[\\[package\\]\\]" uv.lock 2>/dev/null || echo '0')"

# Build the package
build: check-uv
	@echo "📦 Building package..."
	uv build
	@echo "✅ Package built successfully"

# Show project status
status:
	@echo "📊 Invoice Generator Status"
	@echo "=========================="
	@echo "Python version: $(shell python --version 2>/dev/null || echo 'Not found')"
	@echo "UV version: $(shell uv --version 2>/dev/null || echo 'Not installed')"
	@echo "Virtual env: $(shell [ -d .venv ] && echo 'Present' || echo 'Missing')"
	@echo "Config file: $(shell [ -f .env ] && echo 'Present' || echo 'Missing')"
	@echo "Generated invoices: $(shell ls invoices/*.pdf 2>/dev/null | wc -l) files"
	@echo ""

# Development workflow - run all checks
check-all: lint typecheck test
	@echo "✅ All checks passed!"

# Quick start for new users
quickstart:
	@echo "🚀 Quick Start Guide"
	@echo "==================="
	@echo ""
	@echo "1. Install UV and dependencies:"
	@echo "   make setup"
	@echo ""
	@echo "2. Try the demo (no configuration needed):"
	@echo "   make demo"
	@echo ""
	@echo "3. Configure for your business:"
	@echo "   - Edit .env file with your company details"
	@echo "   - Set up Microsoft Graph API (optional, for email)"
	@echo ""
	@echo "4. Generate real invoices:"
	@echo "   make run"
	@echo ""

# Generate sample invoices for different scenarios
samples: check-uv
	@echo "📄 Generating sample invoices for different scenarios..."
	uv run python generate_samples.py