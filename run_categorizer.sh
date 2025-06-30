#!/bin/bash
# Script to run email categorizer

# Navigate to the script directory
cd "$(dirname "$0")"

# Activate Python environment if needed
# source /path/to/your/venv/bin/activate

# Run the categorizer
python3 email_categorizer.py

# Log the run
echo "$(date): Email categorization completed" >> categorization.log
