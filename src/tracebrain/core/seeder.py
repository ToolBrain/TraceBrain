"""Database seeding helpers for TraceBrain."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


def get_samples_dir() -> Path:
    """Return the packaged samples directory path."""
    return Path(__file__).resolve().parent.parent / "resources" / "samples"


def _iter_sample_files(samples_dir: Path) -> Iterable[Path]:
    if not samples_dir.exists():
        logger.warning("Samples directory not found: %s", samples_dir)
        return []
    return sorted(samples_dir.glob("*.json"))


def seed_data(store) -> None:
    """Seed the TraceStore with bundled sample traces."""
    samples_dir = get_samples_dir()
    sample_files = list(_iter_sample_files(samples_dir))
    if not sample_files:
        logger.warning("No sample traces found to seed.")
        return

    success_count = 0
    failure_count = 0

    for sample in sample_files:
        try:
            logger.info("Ingesting sample %s...", sample.name)
            payload = json.loads(sample.read_text(encoding="utf-8"))
            store.add_trace_from_dict(payload)
            success_count += 1
        except Exception as exc:
            failure_count += 1
            logger.exception("Failed to seed sample trace %s: %s", sample.name, exc)

    logger.info(
        "Seeding summary: %s succeeded, %s failed (total %s)",
        success_count,
        failure_count,
        len(sample_files),
    )


def seed_if_empty(store) -> None:
    """Seed the TraceStore if no traces exist."""
    try:
        existing = store.count_traces()
    except Exception:
        logger.exception("Failed to check existing traces")
        return

    if existing and existing > 0:
        return

    samples_dir = get_samples_dir()
    sample_files = list(_iter_sample_files(samples_dir))
    logger.info("Database is empty. Automatically seeding %s sample traces...", len(sample_files))
    seed_data(store)
