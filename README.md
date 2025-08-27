# EDIT

Prototype pipeline for semi-automatic video processing: download → speed → cut → ASR → translate → render. Backend uses FastAPI with RQ workers and a minimalist htmx UI.

## Quick start

```bash
# install deps
pip install -r backend/requirements.txt

# start redis (or use docker)
./scripts/dev_redis.sh &

# run API
uvicorn backend.app.main:app --reload

# run worker
./scripts/run_worker.sh
```

Open http://localhost:8000/ to submit jobs and monitor progress.
