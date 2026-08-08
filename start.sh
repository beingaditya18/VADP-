#!/usr/bin/env bash

echo "============================================================"
echo "          VADP Zero-Trust Legal AI Platform"
echo "             Launching Localhost Services"
echo "============================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "[1/2] Starting FastAPI Backend on http://localhost:8000 ..."
(cd "$SCRIPT_DIR/backend" && python3 -m uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

sleep 3

echo "[2/2] Starting Next.js Frontend on http://localhost:3000 ..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "============================================================"
echo "  SUCCESS! Localhost services started:"
echo "    - Frontend Portal:  http://localhost:3000"
echo "    - Backend REST API: http://localhost:8000"
echo "    - API Docs:        http://localhost:8000/docs"
echo "============================================================"
echo "Press Ctrl+C to terminate both servers."

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
