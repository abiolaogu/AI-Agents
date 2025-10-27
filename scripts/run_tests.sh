#!/bin/bash
# scripts/run_tests.sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Installing test dependencies..."
pip install pytest requests celery redis

echo "Running tests for the Orchestration Engine..."
# Set PYTHONPATH to include the root directory so imports work
export PYTHONPATH=$(pwd)
python3 -m pytest services/orchestration_engine/tests/

echo "Running tests for the SEO Agent..."
python3 -m pytest services/seo_agent/tests/

echo "All tests passed!"
