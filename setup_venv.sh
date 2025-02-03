#!/usr/bin/env bash

# Get the directory this script is in
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Create virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Install/upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r "$SCRIPT_DIR/requirements.txt"

echo -e "\npaperless-ngx-postprocessor setup successful"
