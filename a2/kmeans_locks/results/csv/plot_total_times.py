#!/usr/bin/env python3
"""
Plot total timing results for all lock experiments on a single graph.
Reads every total_*.csv file in this directory, assuming the first row
contains thread counts and the second row contains total time values.
"""

import csv
import glob
import os
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt

DATA_PATTERN = "total_*.csv"
OUTPUT_FILE = "total_times.png"


def _prettify_label(filename: str) -> str:
    """Turn total_array_lock.csv into Array Lock for nicer legends."""
    name = filename
    if name.startswith("total_"):
        name = name[len("total_") :]
    if name.endswith(".csv"):
        name = name[: -len(".csv")]
    return name.replace("_", " ").title()


def load_totals(pattern: str) -> Tuple[List[int], Dict[str, Tuple[List[int], List[float]]]]:
    data: Dict[str, Tuple[List[int], List[float]]] = {}
    common_threads: Optional[List[int]] = None

    for path in sorted(glob.glob(pattern)):
        with open(path, newline="") as csvfile:
            rows = list(csv.reader(csvfile))
        if len(rows) < 2:
            raise ValueError(f"Expected at least 2 rows in {path}, got {len(rows)}")

        threads = [int(value) for value in rows[0] if value.strip()]
        times = [float(value) for value in rows[1] if value.strip()]

        if common_threads is None:
            common_threads = threads
        elif threads != common_threads:
            raise ValueError(f"Thread counts mismatch in {path}: {threads} vs {common_threads}")

        label = _prettify_label(os.path.basename(path))
        data[label] = (threads, times)

    if common_threads is None:
        raise RuntimeError(f"No CSV files matched pattern {pattern}")

    return common_threads, data


def main() -> None:
    threads, datasets = load_totals(DATA_PATTERN)

    plt.figure(figsize=(8, 5))
    for label, (thread_counts, times) in datasets.items():
        plt.plot(thread_counts, times, marker="o", label=label)

    plt.xlabel("Thread count")
    plt.ylabel("Total time (sec)")
    plt.title("KMeans Lock Timing vs Thread Count")
    plt.xticks(threads)
    plt.grid(True, linestyle="--", linewidth=0.7, alpha=0.6)
    plt.legend(title="Lock type")
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=150)
    print(f"Saved plot to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
