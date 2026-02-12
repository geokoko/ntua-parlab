#!/usr/bin/env python3
"""
Speedup plots for Jacobi MPI (constant iterations, no convergence check)
Sizes: 2048x2048, 4096x4096, 6144x6144
MPI processes: 1, 2, 4, 8, 16, 32, 64
"""

import matplotlib.pyplot as plt
import os
import re
from pathlib import Path

# LaTeX-like font
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman', 'DejaVu Serif'],
    'mathtext.fontset': 'cm',
    'axes.labelsize': 12,
    'font.size': 11,
    'legend.fontsize': 10,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
})

# Base paths
base_dir = Path(__file__).resolve().parent
project_dir = (base_dir / '..' / 'heat_transfer').resolve()
mpi_results_dir = project_dir / 'jacobi' / 'mpi' / 'jac_results'
output_dir = base_dir / 'plots' / 'jacobi_only'

# Sizes and MPI processes
sizes = [2048, 4096, 6144]
mpi_procs = [1, 2, 4, 8, 16, 32, 64]


def parse_mpi_result(filepath):
    """Parse MPI result file and return TotalTime"""
    with open(filepath, 'r') as f:
        line = f.readline()
        match = re.search(r'TotalTime ([\d.]+)', line)
        if match:
            return float(match.group(1))
    return None


# Parse MPI results and compute speedups (baseline = p=1 MPI)
for size in sizes:
    mpi_times = []
    for nprocs in mpi_procs:
        mpi_file = mpi_results_dir / str(size) / f'mpi_jacobi_constant_{nprocs}.out'
        mpi_time = parse_mpi_result(mpi_file)
        mpi_times.append(mpi_time)

    if not mpi_times or mpi_times[0] is None:
        print(f"Missing p=1 time for size {size}, skipping.")
        continue

    base_time = mpi_times[0]
    speedups = [base_time / t if t else None for t in mpi_times]

    for nprocs, t, s in zip(mpi_procs, mpi_times, speedups):
        if t is None:
            continue
        print(f"Size {size}, {nprocs} procs: MPI time = {t:.4f}s, Speedup = {s:.2f}")

    # Create plot
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.plot(mpi_procs, speedups, 'o-', linewidth=2, markersize=8, label='Jacobi', color='#3498db')

    ax.set_xlabel('MPI Processes', fontsize=12)
    ax.set_ylabel('Speedup', fontsize=12)
    ax.set_title(f'Speedup for Grid {size}x{size}', fontsize=14, fontweight='bold')

    ax.set_xticks(mpi_procs)
    ax.set_xticklabels([str(p) for p in mpi_procs])

    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    output_path = output_dir / f'speedup_{size}.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")

    plt.close()

print("\nAll plots generated successfully!")
