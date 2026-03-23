from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import random

app = FastAPI(title="StreamOps API", version="1.0.0")

# --- Prometheus metrics ---
REQUEST_COUNT = Counter(
    "streamops_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "streamops_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"]
)
ACTIVE_STREAMS = Counter(
    "streamops_active_streams_total",
    "Total streams served"
)

# --- Fake stream data ---
STREAMS = [
    {"id": "s1", "title": "TF1 Direct", "quality": "1080p", "viewers": 142000},
    {"id": "s2", "title": "JT 20h",     "quality": "1080p", "viewers": 98000},
    {"id": "s3", "title": "Koh-Lanta",  "quality": "4K",    "viewers": 310000},
    {"id": "s4", "title": "TF1+",       "quality": "4K",    "viewers": 75000},
]


@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
    return response


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/streams")
def list_streams():
    ACTIVE_STREAMS.inc(len(STREAMS))
    # Simulate slight latency variation
    time.sleep(random.uniform(0.01, 0.05))
    return {"streams": STREAMS, "total": len(STREAMS)}


@app.get("/streams/{stream_id}")
def get_stream(stream_id: str):
    stream = next((s for s in STREAMS if s["id"] == stream_id), None)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return stream


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
