#!/bin/bash
# Setup script for home environment

echo "🏠 Setting up HOME workflow environment..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

# Install dependencies
echo "→ Installing Python dependencies..."
pip install requests pyyaml flask

# Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not set!"
    echo "   Add to ~/.bashrc: export GITHUB_TOKEN=ghp_your_token"
fi

# Download workflow scripts
echo "→ Downloading workflow scripts..."
mkdir -p conversion-tools
cd conversion-tools

# Download scripts (replace with actual URLs)
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/workflow.py
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/visibility-server.py

chmod +x workflow.py visibility-server.py
cd ..

# Initialize
echo "→ Initializing workflow..."
python conversion-tools/workflow.py init

echo "✅ Home setup complete!"
echo ""
echo "Next steps:"
echo "1. Set GITHUB_TOKEN in ~/.bashrc"
echo "2. Update .workflow-config.yaml"
echo "3. Start server: python conversion-tools/visibility-server.py"