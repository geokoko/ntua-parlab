#!/usr/bin/env python3
"""
Speedup plots for Jacobi MPI (constant iterations, no convergence check)
Sizes: 2048x2048, 4096x4096, 6144x6144
MPI processes: 1, 2, 4, 8, 16, 32, 64
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import re

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
base_dir = os.path.dirname(__file__)
serial_results_path = os.path.join(base_dir, '..', 'serial', 'serial_results', 'serial_constant_1.out')
mpi_results_dir = os.path.join(base_dir, '..', 'mpi', 'jac_results')
output_dir = os.path.join(base_dir, 'plots')

# Sizes and MPI processes
sizes = [2048, 4096, 6144]
mpi_procs = [1, 2, 4, 8, 16, 32, 64]

def parse_serial_results(filepath):
    """Parse serial results file and return dict of {size: time}"""
    serial_times = {}
    with open(filepath, 'r') as f:
        for line in f:
            # Format: Jacobi X 2048 Y 2048 Iter 255 Time 7.478101 midpoint 0.000000
            match = re.search(r'Jacobi X (\d+) Y \d+ Iter \d+ Time ([\d.]+)', line)
            if match:
                size = int(match.group(1))
                time = float(match.group(2))
                serial_times[size] = time
    return serial_times

def parse_mpi_result(filepath):
    """Parse MPI result file and return TotalTime"""
    with open(filepath, 'r') as f:
        line = f.readline()
        # Format: Jacobi X 2048 Y 2048 Px 1 Py 1 Iter 256 ComputationTime 8.416434 TotalTime 8.416583 midpoint 0.000000
        match = re.search(r'TotalTime ([\d.]+)', line)
        if match:
            return float(match.group(1))
    return None

# Parse serial results
serial_times = parse_serial_results(serial_results_path)
print("Serial times:", serial_times)

# Parse MPI results and compute speedups
for size in sizes:
    mpi_times = []
    speedups = []
    
    serial_time = serial_times[size]
    
    for nprocs in mpi_procs:
        mpi_file = os.path.join(mpi_results_dir, str(size), f'mpi_jacobi_constant_{nprocs}.out')
        mpi_time = parse_mpi_result(mpi_file)
        mpi_times.append(mpi_time)
        speedup = serial_time / mpi_time
        speedups.append(speedup)
        print(f"Size {size}, {nprocs} procs: MPI time = {mpi_time:.4f}s, Speedup = {speedup:.2f}")
    
    # Create plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(mpi_procs, speedups, 'o-', linewidth=2, markersize=8, label='Jacobi', color='#3498db')
    
    # Ideal speedup line (optional reference)
    # ax.plot(mpi_procs, mpi_procs, '--', linewidth=1, color='gray', alpha=0.5, label='Ideal')
    
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
    output_path = os.path.join(output_dir, f'speedup_{size}.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    
    plt.close()

print("\nAll plots generated successfully!")
