#!/bin/bash
# Setup script for Research Board Backend

echo "🚀 Setting up Research Board Backend..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python 3.8 or higher is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file from .env.example"
    echo "📝 Please review and update the .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Create database directory
mkdir -p data
echo "✅ Created data directory for SQLite database"

echo ""
echo "🎉 Setup complete! 🎉"
echo ""
echo "To start the development server:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the development server: python run_dev.py"
echo ""
echo "Or use the quick start command:"
echo "  source venv/bin/activate && python run_dev.py"
echo ""
echo "API Documentation will be available at: http://127.0.0.1:8000/api/v1/docs"
