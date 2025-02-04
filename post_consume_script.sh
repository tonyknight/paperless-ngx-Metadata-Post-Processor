#!/usr/bin/env bash

# Exit on error
set -e

# Get the directory this script is in
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: $SCRIPT_DIR"

# Function to check Python dependencies
check_dependencies() {
    # Check if PyPDF2 is installed
    if ! python3 -c "import PyPDF2" 2>/dev/null; then
        echo "PyPDF2 not found, setting up environment..."
        return 1
    fi
    if ! python3 -c "import requests" 2>/dev/null; then
        echo "requests not found, setting up environment..."
        return 1
    fi
    return 0
}

# Function to setup environment
setup_environment() {
    echo "Setting up Python environment..."
    # Install pip if needed
    python3 -m ensurepip --upgrade
    
    # Use our requirements file, not Paperless's
    REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo "ERROR: requirements.txt not found at $REQUIREMENTS_FILE"
        exit 1
    }
    
    echo "Installing requirements from: $REQUIREMENTS_FILE"
    python3 -m pip install --user -r "$REQUIREMENTS_FILE"
    
    # Verify installation
    if ! check_dependencies; then
        echo "Failed to install required dependencies"
        exit 1
    fi
    echo "Environment setup complete"
}

# Print debug info about our environment
echo "Script location debugging:"
echo "Current working directory: $(pwd)"
echo "Directory contents of $SCRIPT_DIR:"
ls -la "$SCRIPT_DIR"

# Check and setup environment if needed
if ! check_dependencies; then
    setup_environment
fi

# Print environment variables for debugging
echo "Checking environment..."
echo "DOCUMENT_ID: $1"
echo "DOCUMENT_SOURCE_PATH: $3"
echo "PAPERLESS_URL: $PAPERLESS_URL"

# Verify Python script exists
PYTHON_SCRIPT="$SCRIPT_DIR/pdf_metadata_sync.py"
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Python script not found at $PYTHON_SCRIPT"
    ls -la "$SCRIPT_DIR"
    exit 1
fi

# Run the PDF metadata sync script
echo "Running PDF metadata sync..."
python3 "$PYTHON_SCRIPT" "$1" "$3"

