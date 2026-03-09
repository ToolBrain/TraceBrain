"""Performance and scalability experiments for TraceBrain."""

from __future__ import annotations

import asyncio
import gc
import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import aiohttp
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

from tracebrain.sdk.client import TraceScope

# Ensure background evaluation stays off during benchmarks.
os.environ["AUTO_EVALUATE_TRACES"] = "false"

API_BASE_URL = os.getenv("TRACEBRAIN_API_URL", "http://localhost:8000").rstrip("/")


@dataclass
class ReconstructionPoint:
    steps: int
    time_ms: float


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


def _iso_time(offset_ms: int) -> str:
    now = datetime.now(timezone.utc) + timedelta(milliseconds=offset_ms)
    return now.isoformat().replace("+00:00", "Z")


def build_trace_payload(steps: int) -> Dict[str, Any]:
    spans = []
    parent_id = None
    for i in range(steps):
        span_id = uuid.uuid4().hex[:16]
        spans.append(
            {
                "span_id": span_id,
                "parent_id": parent_id,
                "name": "LLM Inference",
                "start_time": _iso_time(i * 2),
                "end_time": _iso_time(i * 2 + 1),
                "attributes": {
                    "tracebrain.span.type": "llm_inference",
                    "tracebrain.llm.new_content": json.dumps(
                        [{"role": "user", "content": f"step {i}"}]
                    ),
                },
            }
        )
        parent_id = span_id

    return {
        "trace_id": uuid.uuid4().hex,
        "attributes": {"system_prompt": "Synthetic trace"},
        "spans": spans,
    }


def benchmark_reconstruction() -> List[ReconstructionPoint]:
    sizes = [1, 50, 100, 200, 300, 400, 500]
    points: List[ReconstructionPoint] = []
    warmup_runs = 100
    measured_runs = 500

    for size in sizes:
        trace_data = build_trace_payload(size)
        for _ in range(warmup_runs):
            _ = TraceScope.to_messages(trace_data)

        gc.disable()
        durations_ns = []
        for _ in range(measured_runs):
            start = time.perf_counter_ns()
            _ = TraceScope.to_messages(trace_data)
            end = time.perf_counter_ns()
            durations_ns.append(end - start)
        gc.enable()
        avg_ms = float(np.mean(durations_ns)) / 1_000_000
        points.append(ReconstructionPoint(steps=size, time_ms=avg_ms))

    return points


async def _post_trace(
    session: aiohttp.ClientSession,
    payload: Dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> Tuple[bool, float]:
    async with semaphore:
        start = time.perf_counter_ns()
        try:
            async with session.post(f"{API_BASE_URL}/api/v1/traces", json=payload) as resp:
                await resp.text()
                ok = resp.status in (200, 201)
        except Exception:
            ok = False
        end = time.perf_counter_ns()
        return ok, (end - start) / 1_000_000


def _build_ingestion_payload() -> Dict[str, Any]:
    return {
        "trace_id": uuid.uuid4().hex,
        "attributes": {"system_prompt": "load test"},
        "spans": [
            {
                "span_id": uuid.uuid4().hex[:16],
                "parent_id": None,
                "name": "LLM Inference",
                "start_time": _iso_time(0),
                "end_time": _iso_time(1),
                "attributes": {
                    "tracebrain.span.type": "llm_inference",
                    "tracebrain.llm.new_content": json.dumps(
                        [{"role": "user", "content": "ping"}]
                    ),
                },
            },
            {
                "span_id": uuid.uuid4().hex[:16],
                "parent_id": None,
                "name": "Tool Execution: ping",
                "start_time": _iso_time(2),
                "end_time": _iso_time(3),
                "attributes": {
                    "tracebrain.span.type": "tool_execution",
                    "tracebrain.tool.name": "ping",
                    "tracebrain.tool.output": "pong",
                },
            },
            {
                "span_id": uuid.uuid4().hex[:16],
                "parent_id": None,
                "name": "LLM Inference",
                "start_time": _iso_time(4),
                "end_time": _iso_time(5),
                "attributes": {
                    "tracebrain.span.type": "llm_inference",
                    "tracebrain.llm.new_content": json.dumps(
                        [{"role": "assistant", "content": "pong"}]
                    ),
                },
            },
        ],
    }


async def benchmark_ingestion() -> None:
    total_requests = 10_000
    warmup_requests = 200
    concurrency = 50
    semaphore = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession() as session:
        warmup_tasks = []
        for _ in range(warmup_requests):
            warmup_tasks.append(
                _post_trace(session, _build_ingestion_payload(), semaphore)
            )
        await asyncio.gather(*warmup_tasks)

        tasks = []
        for _ in range(total_requests):
            tasks.append(_post_trace(session, _build_ingestion_payload(), semaphore))

        start = time.perf_counter_ns()
        results = await asyncio.gather(*tasks)
        end = time.perf_counter_ns()

    ok_count = sum(1 for ok, _ in results if ok)
    latencies = [lat for _, lat in results]
    total_time_s = (end - start) / 1_000_000_000
    throughput = ok_count / total_time_s if total_time_s > 0 else 0.0

    avg_latency = float(np.mean(latencies))
    p95_latency = float(np.percentile(latencies, 95))
    p99_latency = float(np.percentile(latencies, 99))

    print("\n| Total Requests | Throughput (RPS) | Avg Latency (ms) | p95 Latency (ms) | p99 Latency (ms) |")
    print("| --- | --- | --- | --- | --- |")
    print(
        f"| {ok_count} | {throughput:.2f} | {avg_latency:.2f} | {p95_latency:.2f} | {p99_latency:.2f} |"
    )

    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "ingestion_metrics.csv"
    metrics_path.write_text(
        "total_requests,throughput_rps,avg_latency_ms,p95_latency_ms,p99_latency_ms\n"
        f"{ok_count},{throughput:.4f},{avg_latency:.4f},{p95_latency:.4f},{p99_latency:.4f}\n"
    )


def plot_reconstruction(points: List[ReconstructionPoint]) -> None:
    configure_plot()

    steps = np.array([p.steps for p in points])
    times = np.array([p.time_ms for p in points])
    slope, intercept, _, _, _ = linregress(steps, times)
    fit = slope * steps + intercept

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(steps, times, "o", color="#1f77b4", label="Measured")
    ax.plot(steps, fit, "-", color="#444444", label="Linear fit")
    ax.set_xlabel("Number of Steps (N)")
    ax.set_ylabel("Reconstruction Time (ms)")
    ax.legend(frameon=True)
    fig.tight_layout()
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "reconstruction_scaling.pdf", format="pdf")
    metrics = np.column_stack([steps, times, fit])
    np.savetxt(
        output_dir / "reconstruction_scaling.csv",
        metrics,
        delimiter=",",
        header="steps,time_ms,linear_fit_ms",
        comments="",
    )


def main() -> None:
    points = benchmark_reconstruction()
    plot_reconstruction(points)

    asyncio.run(benchmark_ingestion())


if __name__ == "__main__":
    main()
