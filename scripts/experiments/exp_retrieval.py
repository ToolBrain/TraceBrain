"""Experience retrieval scalability experiment (pgvector search)."""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from tracebrain.db.base import Trace, TraceStatus


@dataclass
class RetrievalPoint:
    traces_k: int
    p50_ms: float
    p90_ms: float
    p95_ms: float


def configure_plot() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "axes.grid": False,
        }
    )


def resolve_db_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    user = os.getenv("POSTGRES_USER", "tracebrain")
    password = os.getenv("POSTGRES_PASSWORD", "tracebrain_2026_secure")
    db = os.getenv("POSTGRES_DB", "tracestore")
    return f"postgresql://{user}:{password}@localhost:5432/{db}"


def seed_traces(engine, target_count: int, batch_size: int = 5000) -> None:
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        existing = int(session.query(func.count(Trace.id)).scalar() or 0)

    remaining = max(target_count - existing, 0)
    if remaining == 0:
        return

    SessionLocal = sessionmaker(bind=engine)
    dim = Trace.__table__.columns["embedding"].type.dim

    while remaining > 0:
        batch = min(batch_size, remaining)
        embeddings = np.random.normal(size=(batch, dim)).astype(float)
        rows: List[Trace] = []
        now = datetime.now(timezone.utc)
        for i in range(batch):
            trace_id = uuid.uuid4().hex
            rows.append(
                Trace(
                    id=trace_id,
                    system_prompt="Synthetic trace",
                    episode_id=None,
                    created_at=now,
                    status=TraceStatus.completed,
                    priority=3,
                    embedding=embeddings[i].tolist(),
                    attributes={"system_prompt": "Synthetic trace"},
                    feedback={"rating": 5},
                    ai_evaluation=None,
                )
            )
        with SessionLocal() as session:
            session.bulk_save_objects(rows)
            session.commit()
        remaining -= batch


def format_points(points: List[RetrievalPoint]) -> Dict[str, List[float]]:
    x_vals = [p.traces_k for p in points]
    p50s = [p.p50_ms for p in points]
    p90s = [p.p90_ms for p in points]
    p95s = [p.p95_ms for p in points]
    return {"x": x_vals, "p50": p50s, "p90": p90s, "p95": p95s}


async def benchmark_search(latency_points: List[RetrievalPoint]) -> None:
    async with aiohttp.ClientSession() as session:
        for point in latency_points:
            latencies = []
            for _ in range(100):
                start = time.perf_counter_ns()
                async with session.get(
                    "http://localhost:8000/api/v1/traces/search",
                    params={"text": "tool execution error", "min_rating": 4, "limit": 3},
                ) as resp:
                    await resp.text()
                end = time.perf_counter_ns()
                latencies.append((end - start) / 1_000_000)

            point.p50_ms = float(np.percentile(latencies, 50))
            point.p90_ms = float(np.percentile(latencies, 90))
            point.p95_ms = float(np.percentile(latencies, 95))


def plot_retrieval(points: List[RetrievalPoint]) -> None:
    configure_plot()
    data = format_points(points)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(data["x"], data["p50"], "o-", color="#1f77b4", label="P50 latency")
    ax.plot(data["x"], data["p90"], "s-", color="#2ca02c", label="P90 latency")
    ax.plot(data["x"], data["p95"], "^-", color="#b22222", label="P95 latency")
    ax.set_xlabel("Number of Traces in Database (k)")
    ax.set_ylabel("Search Latency (ms)")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=True)
    fig.tight_layout()
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "retrieval_scalability.pdf", format="pdf")
    csv_lines = ["traces_k,p50_ms,p90_ms,p95_ms"]
    for point in points:
        csv_lines.append(
            f"{point.traces_k},{point.p50_ms:.4f},{point.p90_ms:.4f},{point.p95_ms:.4f}"
        )
    (output_dir / "retrieval_scalability.csv").write_text("\n".join(csv_lines))


def main() -> None:
    db_url = resolve_db_url()
    engine = create_engine(db_url)

    milestones = [10_000, 50_000, 100_000]
    points: List[RetrievalPoint] = []

    for milestone in milestones:
        seed_traces(engine, milestone, batch_size=5000)
        points.append(RetrievalPoint(traces_k=milestone // 1000, p50_ms=0.0, p90_ms=0.0, p95_ms=0.0))

    asyncio.run(benchmark_search(points))
    plot_retrieval(points)


if __name__ == "__main__":
    main()
