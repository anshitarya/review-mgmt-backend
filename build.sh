#!/bin/bash
# Build script for Render deployment
set -e

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build complete!"
