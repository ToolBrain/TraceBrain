"""Storage efficiency benchmark: naive logging vs TraceBrain delta."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class StoragePoint:
    steps: int
    naive_mb: float
    delta_mb: float


def compute_storage(points: List[int]) -> List[StoragePoint]:
    system_bytes = 4000
    step_bytes = 800
    results: List[StoragePoint] = []

    for n in points:
        naive_bytes = n * system_bytes + step_bytes * (n * (n + 1) // 2)
        delta_bytes = system_bytes + n * step_bytes
        results.append(
            StoragePoint(
                steps=n,
                naive_mb=naive_bytes / (1024 * 1024),
                delta_mb=delta_bytes / (1024 * 1024),
            )
        )

    return results


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


def main() -> None:
    configure_plot()

    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    steps = [10, 20, 50, 100, 150, 200]
    data = compute_storage(steps)
    df = pd.DataFrame([d.__dict__ for d in data])

    df.to_csv(output_dir / "delta_vs_naive_storage.csv", index=False)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(
        df["steps"],
        df["naive_mb"],
        color="#b22222",
        marker="o",
        label="Naive logging (O(N^2))",
    )
    ax.plot(
        df["steps"],
        df["delta_mb"],
        color="#1f77b4",
        marker="s",
        label="TraceBrain delta (O(N))",
    )
    ax.set_xlabel("Number of Execution Steps")
    ax.set_ylabel("Cumulative Payload Size (MB)")
    ax.legend(frameon=True)
    fig.tight_layout()
    fig.savefig(output_dir / "delta_vs_naive_storage.pdf", format="pdf")


if __name__ == "__main__":
    main()
