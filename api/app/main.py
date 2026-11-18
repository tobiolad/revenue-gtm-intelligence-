"""
Read-only revenue/GTM analytics API over the DuckDB database built by
`db/load.py`. Every route delegates to db/metrics.py or db/forecast.py --
this file only wires up HTTP, it holds no analysis logic of its own.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import deals, forecast, funnel, overview, reps

app = FastAPI(
    title="Revenue & GTM Operations Intelligence API",
    description="Read-only analytics over a synthetic B2B sales pipeline, including a backtested forecast.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(overview.router)
app.include_router(funnel.router)
app.include_router(reps.router)
app.include_router(deals.router)
app.include_router(forecast.router)


@app.get("/health")
def health():
    return {"status": "ok"}
