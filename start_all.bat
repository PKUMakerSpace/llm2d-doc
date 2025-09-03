@echo off
start cmd /k "cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
start cmd /k "cd frontend && npm run dev"