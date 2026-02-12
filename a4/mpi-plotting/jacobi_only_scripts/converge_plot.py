#!/usr/bin/env python3
"""
Jacobi MPI convergence breakdown (512x512, 64 MPI processes)
"""

import matplotlib.pyplot as plt
import numpy as np
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

base_dir = Path(__file__).resolve().parent
project_dir = (base_dir / '..' / 'heat_transfer').resolve()
mpi_result_file = project_dir / 'jacobi' / 'mpi' / 'jac_results' / 'mpi_jacobi_converge.out'
output_dir = base_dir / 'plots' / 'jacobi_only'


def parse_mpi_result(filepath):
    with open(filepath, 'r') as f:
        lines = f.read().splitlines()
        if not lines:
            return None
        first = lines[0]
        comp_match = re.search(r'ComputationTime ([\d.]+)', first)
        total_match = re.search(r'TotalTime ([\d.]+)', first)
        if not comp_match or not total_match:
            return None
        comp_time = float(comp_match.group(1))
        total_time = float(total_match.group(1))

        conv_time = 0.0
        for line in lines[1:]:
            match = re.search(r'Total converge time\s+([\d.]+)', line)
            if match:
                conv_time = float(match.group(1))
                break
        return comp_time, conv_time, total_time


result = parse_mpi_result(mpi_result_file)
if result is None:
    print("Missing converge results.")
    raise SystemExit(1)

mpi_computation_time, mpi_converge_time, mpi_total_time = result
mpi_other_time = mpi_total_time - mpi_computation_time - mpi_converge_time

# Create plot
fig, ax = plt.subplots(figsize=(8, 6))

x = np.array([0])
width = 0.5

# Stacked bar: Computation -> Converge -> Other
ax.bar(x, mpi_computation_time, width, label='Computation Time', color='#3498db')
ax.bar(x, mpi_converge_time, width, bottom=mpi_computation_time,
       label='Converge Time', color='#e74c3c')
ax.bar(x, mpi_other_time, width, bottom=mpi_computation_time + mpi_converge_time,
       label='Other', color='#f39c12')

# Total label
ax.text(x[0], mpi_total_time + mpi_total_time * 0.05, f'{mpi_total_time:.2f}s',
        ha='center', va='bottom', fontsize=11, fontweight='bold')

# Axis settings
ax.set_ylabel('Time (seconds)', fontsize=12)
ax.set_title('With Converge (512x512, 64 MPI Processes)',
             fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(['Jacobi'], fontsize=11)

ax.legend(loc='upper right', fontsize=10)
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)
ax.set_ylim(0, mpi_total_time * 1.1)

plt.tight_layout()

# Save plot
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / 'converge_512_p64.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Plot saved to: {output_path}")
