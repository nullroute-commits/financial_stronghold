#!/bin/bash
# Setup development environment
# This script creates a virtual environment and installs dependencies

set -e

echo "=== Development Environment Setup ==="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.12 or higher"
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Check if we can create virtual environment
if ! python3 -m venv --help &> /dev/null; then
    echo "⚠️  Python venv module not available"
    echo "On Debian/Ubuntu, install with: sudo apt-get install python3-venv"
    echo "On RHEL/CentOS, install with: sudo yum install python3-virtualenv"
    exit 1
fi

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing..."
    rm -rf venv
fi

echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "📦 Installing development dependencies..."
if [ -f "requirements/development.txt" ]; then
    pip install -r requirements/development.txt
else
    echo "❌ requirements/development.txt not found"
    exit 1
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"