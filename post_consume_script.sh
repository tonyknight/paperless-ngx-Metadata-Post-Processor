#!/usr/bin/env bash

# Exit on error
set -e

# Get the directory this script is in
RUN_DIR=$( dirname -- "$( readlink -f -- "$0"; )"; )

# Function to check Python dependencies
check_dependencies() {
    # Check if PyPDF2 is installed
    if ! python3 -c "import PyPDF2" 2>/dev/null; then
        echo "PyPDF2 not found, setting up environment..."
        return 1
    fi
    # Check if requests is installed
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
    # Install required packages
    python3 -m pip install --user -r "$RUN_DIR/requirements.txt"
    # Verify installation
    if ! check_dependencies; then
        echo "Failed to install required dependencies"
        exit 1
    fi
    echo "Environment setup complete"
}

# Check and setup environment if needed
if ! check_dependencies; then
    setup_environment
fi

# Parse arguments from Paperless
# $1: Document ID
# $2: Filename
# $3: Source path
# $4: Thumbnail path
# $5: Download URL
# $6: Thumbnail URL
# $7: Task ID
export DOCUMENT_ID="$1"
export DOCUMENT_SOURCE_PATH="$3"

# Set API URL if not already set
if [ -z "$PAPERLESS_URL" ]; then
    export PAPERLESS_URL="http://localhost:8000/api"
fi

# Verify environment
echo "Checking environment..."
echo "DOCUMENT_ID: $DOCUMENT_ID"
echo "DOCUMENT_SOURCE_PATH: $DOCUMENT_SOURCE_PATH"
echo "PAPERLESS_URL: $PAPERLESS_URL"

# Check required variables
if [ -z "$DOCUMENT_ID" ] || [ -z "$DOCUMENT_SOURCE_PATH" ]; then
    echo "Error: Required arguments not provided"
    echo "Usage: $0 <document_id> <filename> <source_path> <thumbnail_path> <download_url> <thumbnail_url> <task_id>"
    exit 1
fi

# Run the PDF metadata sync
echo "Running PDF metadata sync..."
python3 "$RUN_DIR/pdf_metadata_sync.py"

