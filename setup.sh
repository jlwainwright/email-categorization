#!/bin/bash
# Setup script for email categorization

echo "Setting up Email Categorization System..."

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install Python 3 and pip before continuing."
    exit 1
fi

# Install required packages
echo "Installing required Python packages..."
pip3 install -r requirements.txt

# Check if config exists
if [ -f "config.ini" ]; then
    echo ""
    echo "Configuration file found. Setting up encryption..."
    python3 setup_encryption.py
else
    echo ""
    echo "Setup complete!"
    echo ""
    echo "Choose setup method:"
    echo "1. Guided setup wizard (recommended): python3 setup_provider.py"
    echo "2. Manual configuration: Create config.ini and run python3 setup_encryption.py"
    echo ""
    echo "After setup, run ./run_categorizer.sh to start categorizing emails."
    echo ""
    echo "To see supported providers: python3 setup_provider.py --provider-info"
fi
