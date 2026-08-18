#!/bin/bash

echo "=============================================="
echo "Running S3 Bucket CRUD Library Unit Tests"
echo "=============================================="

echo "[1/3] Starting MinIO test environment..."
docker compose up -d

echo "[2/3] Running tests with pytest and coverage..."
export COVERAGE_CORE=sysmon

# Automatically activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    echo "Activating virtual environment (Windows path style)..."
    source .venv/Scripts/activate
fi

# Ensure pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Auto-installing from requirements-dev.txt..."
    pip install -r requirements-dev.txt
    
    if ! command -v pytest &> /dev/null; then
        echo "Error: Failed to install pytest. Please check your python environment."
        docker compose down
        exit 1
    fi
fi

export PYTHONPATH="$PWD"
pytest --cov=s3_library --cov-report=term-missing tests/
PYTEST_EXIT_CODE=$?

echo "[3/3] Tearing down MinIO test environment..."
docker compose down

echo "=============================================="
if [ $PYTEST_EXIT_CODE -eq 0 ]; then
    echo -e "\e[32mTest run complete! All tests passed.\e[0m"
else
    echo -e "\e[31mTest run complete! Some tests failed.\e[0m"
fi
echo "=============================================="

exit $PYTEST_EXIT_CODE
