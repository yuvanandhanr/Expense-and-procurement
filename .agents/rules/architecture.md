# Expense & Procurement Project Architecture Guidelines

## 1. Database
- Always use the remote **Supabase PostgreSQL** instance (`aws-1-ap-south-1.pooler.supabase.com`).
- Do not introduce local Postgres container overrides.

## 2. Render Deployment Structure
- **Backend Service**: Deployed as a Docker Web Service running Gunicorn (`gunicorn -c gunicorn_conf.py src.main:app`).
- **Frontend Service**: Deployed as a Static Site building from `frontend/` (`npm run build`, publish path `dist`).
- Do not generate `render.yaml` Blueprint files as the project uses manual Render dashboard configuration with Git CI auto-deploy.

## 3. Environment Variables Mapping
- **Backend**: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_KEY`, `JWT_SECRET`, `TESSERACT_CMD=/usr/bin/tesseract`, `REDIS_URL`, AWS credentials.
- **Frontend**: `VITE_API_URL` (Backend Render URL + `/api/v1`), `VITE_GOOGLE_CLIENT_ID`.
