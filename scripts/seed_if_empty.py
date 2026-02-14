import sys
from pathlib import Path

# Add project root to path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracebrain.config import settings
from tracebrain.core.store import TraceStore
from src.examples.seed_tracestore_samples import seed_tracestore


def main() -> None:
    store = TraceStore(backend=settings.get_backend_type(), db_url=settings.DATABASE_URL)
    existing = store.count_traces()
    if existing > 0:
        print(f"Seed skipped: {existing} traces already exist.")
        return

    samples_dir = ROOT / "data" / "TraceBrain OTLP Trace Samples"
    seed_tracestore(
        backend=settings.get_backend_type(),
        db_url=settings.DATABASE_URL,
        samples_dir=samples_dir,
    )


if __name__ == "__main__":
    main()
