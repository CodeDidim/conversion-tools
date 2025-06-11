#!/bin/bash
# Setup script for company environment

echo "🏢 Setting up COMPANY workflow environment..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

# Install dependencies
echo "→ Installing Python dependencies..."
pip install requests pyyaml

# Download company workflow script
echo "→ Downloading company workflow script..."
mkdir -p conversion-tools
cd conversion-tools

# Download script (replace with actual URL)
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/workflow-company.py

chmod +x workflow-company.py
cd ..

# Initialize
echo "→ Initializing company workflow..."
python conversion-tools/workflow-company.py init

echo "✅ Company setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .workflow-config-company.yaml with server details"
echo "2. Get company_profile.yaml from team"
echo "3. Test: python conversion-tools/workflow-company.py check-server"
echo ""
echo "⚠️  REMEMBER: Never copy workflow.py (home version) here!"