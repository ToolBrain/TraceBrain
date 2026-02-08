"""
Seed the TraceStore with sample trace files.

This script demonstrates how to use the TraceStore to ingest
agent execution traces from JSON files conforming to the
ToolBrain Standard OTLP Trace Schema.

Usage:
        1. Start the backend (Docker): toolbrain-trace up
        2. Run this script: python src/examples/seed_tracestore_samples.py
             Optional overrides:
                 --backend sqlite|postgres
                 --db-url postgresql://user:pass@host:port/db
                 --samples-dir "path/to/ToolBrain OTLP Trace Samples"
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from toolbrain_tracing.core.store import TraceStore
from toolbrain_tracing.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_trace_files(directory: str) -> List[Dict[str, Any]]:
    """
    Load all JSON trace files from a directory.
    
    Args:
        directory (str): Path to the directory containing trace JSON files.
    
    Returns:
        list[dict]: List of parsed trace dictionaries.
    """
    traces = []
    trace_dir = Path(directory)
    
    if not trace_dir.exists():
        logger.error(f"Directory not found: {directory}")
        return traces
    
    # Get all .json files
    json_files = sorted(trace_dir.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON files found in {directory}")
        return traces
    
    logger.info(f"Found {len(json_files)} trace files in {directory}")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                trace_data = json.load(f)
                traces.append(trace_data)
                logger.info(f"✓ Loaded {json_file.name}")
        except Exception as e:
            logger.error(f"✗ Failed to load {json_file.name}: {e}")
    
    return traces


def seed_tracestore(backend: str = "postgres", db_url: str = None, samples_dir: Path = None):
    """
    Seed the TraceStore with sample traces.
    
    Args:
        backend (str): Storage backend ('sqlite' or 'postgres').
        db_url (str): Database connection URL.
    """
    print("=" * 70)
    print("ToolBrain TraceStore Seeding Script")
    print("=" * 70)
    print()
    
    # Determine the path to sample traces
    project_root = Path(__file__).parent.parent.parent
    if samples_dir is None:
        samples_dir = project_root / "data" / "ToolBrain OTLP Trace Samples"
    
    print(f"📂 Loading trace files from: {samples_dir}")
    print()
    
    # Load trace files
    traces = load_trace_files(str(samples_dir))
    
    if not traces:
        logger.error("No traces loaded. Exiting.")
        return
    
    print(f"📦 Loaded {len(traces)} trace files")
    print()
    
    # Initialize TraceStore
    if db_url is None:
        db_url = settings.DATABASE_URL
    if backend is None:
        backend = settings.get_backend_type()

    print(f"🔌 Connecting to {backend} database...")
    try:
        store = TraceStore(backend=backend, db_url=db_url)
        print(f"✓ Connected to {backend} backend")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return
    
    print()
    print("💾 Ingesting traces into TraceStore...")
    print("-" * 70)
    
    # Ingest traces
    success_count = 0
    failed_count = 0
    
    for i, trace_data in enumerate(traces, 1):
        trace_id = trace_data.get("trace_id", "unknown")
        num_spans = len(trace_data.get("spans", []))
        
        try:
            store.add_trace_from_dict(trace_data)
            print(f"✓ [{i}/{len(traces)}] Ingested trace {trace_id} ({num_spans} spans)")
            success_count += 1
        except Exception as e:
            print(f"✗ [{i}/{len(traces)}] Failed to ingest trace {trace_id}: {e}")
            failed_count += 1
    
    # Summary
    print("-" * 70)
    print()
    print("📊 Summary:")
    print(f"   ✓ Successfully ingested: {success_count} traces")
    if failed_count > 0:
        print(f"   ✗ Failed: {failed_count} traces")
    print()
    
    # Query verification
    print("🔍 Verifying ingestion...")
    try:
        all_traces = store.list_traces(limit=100, include_spans=True)
        print(f"✓ Found {len(all_traces)} traces in the database")
        print()
        
        if all_traces:
            print("Sample traces:")
            for trace in all_traces[:5]:
                print(f"   - {trace.id}: {len(trace.spans)} spans")
    except Exception as e:
        logger.error(f"Failed to query traces: {e}")
    
    print()
    print("=" * 70)
    print("✅ Seeding complete!")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the TraceStore with sample traces")
    parser.add_argument(
        "--backend",
        choices=["sqlite", "postgres", "postgresql"],
        default=settings.get_backend_type(),
        help="Storage backend (default: from settings)"
    )
    parser.add_argument(
        "--db-url",
        default=settings.DATABASE_URL,
        help="Database URL (default: from settings)"
    )
    parser.add_argument(
        "--samples-dir",
        default=None,
        help="Path to the sample JSON directory (default: ./data/ToolBrain OTLP Trace Samples)"
    )

    args = parser.parse_args()
    samples_dir = Path(args.samples_dir) if args.samples_dir else None

    seed_tracestore(backend=args.backend, db_url=args.db_url, samples_dir=samples_dir)
