#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Loaded .env"
fi

echo "========================================"
echo "Universal Restrictor API"
echo "========================================"
echo "Starting server on http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Environment:"
echo "  - API_KEYS: $([ -n "$API_KEYS" ] && echo 'configured' || echo 'NOT SET')"
echo "  - ANTHROPIC_API_KEY: $([ -n "$ANTHROPIC_API_KEY" ] && echo 'configured' || echo 'NOT SET')"
echo "  - CORS_ORIGINS: ${CORS_ORIGINS:-'disabled'}"
echo "  - RATE_LIMIT: ${RATE_LIMIT:-60}/min"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"

uvicorn restrictor.api.server:app --host 0.0.0.0 --port 8000 --reload
