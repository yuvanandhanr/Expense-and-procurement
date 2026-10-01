#!/bin/bash
# Start backend
PYTHONPATH=. .venv/bin/gunicorn -c gunicorn_conf.py src.main:app &
BACKEND_PID=$!

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait for Vite to be ready
sleep 5

# Run playwright
npx playwright test tests/e2e/test_bell.spec.ts

# Cleanup
kill $BACKEND_PID
kill $FRONTEND_PID
