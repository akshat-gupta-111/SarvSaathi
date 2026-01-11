#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files (requires WhiteNoise or similar)
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate