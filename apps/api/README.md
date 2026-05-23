# DAMAY API

FastAPI backend. Organizer endpoints + Stellar/Twilio gateway + async Stellar write queue.

## Dev quick start

```bash
cd apps/api
uv sync --extra dev
cp ../../.env.example .env.local
uv run uvicorn main:app --reload --port 8000
# OpenAPI: http://localhost:8000/docs
# Health:  http://localhost:8000/healthz
uv run pytest
```

Mock mode: if `REPUTATION_CONTRACT_ID` / `PALUWAGAN_CONTRACT_ID` are unset, the Stellar client returns synthetic success (dev + demo until live deploy).
