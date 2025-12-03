# Backend Implementation Plan (derived from root plan.md)

This file contains a concrete, actionable backend plan derived from the project's root `plan.md`.

Goals
- Build FastAPI-based backend with sync & async TTS endpoints
- Provide Celery-ready task wiring for async jobs
- Integrate with Piper HTTP server for CPU voice synthesis
- Provide simple auth skeleton (JWT) and DB placeholders

Milestones
1) Sprint 1 — Starter skeleton (this commit)
   - FastAPI app with health, voices, `/tts/sync` proxy
   - Config via environment variables
   - Dockerfile + requirements
   - Basic README and run instructions

2) Sprint 1.1 — Async job wiring
   - Celery config, tasks, Redis connection
   - Job and chunk DB models (placeholder SQLAlchemy)
   - Endpoint `/tts/jobs` to create jobs

3) Sprint 2 — Chunking & merging
   - Implement sentence segmentation and chunk builder
   - Worker logic to call Piper for each chunk and upload to S3
   - FFmpeg merge step

4) Sprint 3 — Parler GPU integration
   - GPU worker queue
   - Model loading and retry logic

Execution notes
- This starter skeleton focuses on low-risk, high-value pieces: a proxyable sync endpoint and the project structure needed for Celery integration.
- Piper HTTP server URL is configurable via `PIPER_URL` (default: http://piper-service:5000/synthesize)

Acceptance criteria (for this sprint)
- GET `/health` returns 200
- GET `/voices` returns a JSON list (can be seeded from `piper docs/VOICES.md`)
- POST `/tts/sync` accepts JSON and proxies to configured Piper server, returning audio bytes and correct Content-Type

Next actions
- Implement async job endpoints and add Celery worker scaffolding
- Add unit tests for chunking and proxy behavior
