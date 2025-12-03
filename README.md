# Backend - Starter

This folder contains a minimal FastAPI backend skeleton for the TTS app.

How to run (dev)

1. Install deps

```powershell
python -m venv .venv; .\.venv\Scripts\activate; pip install -r requirements.txt
```

2. Start the app

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Configure Piper

By default the app expects a Piper HTTP server at `http://piper-service:5000/synthesize`. Set `PIPER_URL` in a `.env` file to change.

Notes:
- Local Piper (installed via `python -m piper.http_server`) expects POSTs to `/` (root). Some Piper deployments or images expose `/synthesize` — set `PIPER_URL` accordingly.
- To run Celery worker (after you have Redis):

```powershell
# from project root
docker compose -f backend/docker-compose.dev.yml up -d redis
# start worker in a separate shell (requires celery installed)
celery -A celery_worker.celery_app worker --loglevel=info
```

Schema note (dev):
- I added a `text` column to the `jobs` table required by the worker pipeline. If you already have `backend/dev.db` from earlier runs, either:
	- remove `backend/dev.db` so the app recreates tables on next startup, or
	- run a simple migration (not included) to add the `text` column.

To remove and recreate the DB for development:

```powershell
Remove-Item .\backend\dev.db -Force
# then restart the backend uvicorn so it recreates tables
uvicorn app.main:app --reload --port 8000
```
