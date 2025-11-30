#!/bin/bash

echo "Running Bandit Security Scan..."
bandit -r services/orchestration_engine -ll

echo "Running Safety Dependency Check..."
safety check -r services/orchestration_engine/requirements.txt

echo "Security Scans Completed."
