#!/bin/bash
# Run the Universal Restrictor API locally (without Docker)
#
# Usage:
#   ./run.sh          # Run on default port 8000
#   ./run.sh 8080     # Run on custom port

set -e

PORT=${1:-8000}

echo "========================================"
echo "Universal Restrictor API"
echo "========================================"
echo ""
echo "Starting server on http://localhost:$PORT"
echo "API docs: http://localhost:$PORT/docs"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

uvicorn restrictor.api.server:app --host 0.0.0.0 --port $PORT --reload
