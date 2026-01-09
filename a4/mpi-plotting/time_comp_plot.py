#!/usr/bin/env python3
"""
Bar plots: Total Time vs Computation Time for Jacobi MPI
Sizes: 2048x2048, 4096x4096, 6144x6144
MPI processes: 8, 16, 32, 64
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
mpi_results_dir = os.path.join(base_dir, '..', 'mpi', 'jac_results')
output_dir = os.path.join(base_dir, 'plots')

# Sizes and MPI processes
sizes = [2048, 4096, 6144]
mpi_procs = [8, 16, 32, 64]

def parse_mpi_result(filepath):
    """Parse MPI result file and return (ComputationTime, TotalTime)"""
    with open(filepath, 'r') as f:
        line = f.readline()
        # Format: Jacobi X 2048 Y 2048 Px 1 Py 1 Iter 256 ComputationTime 8.416434 TotalTime 8.416583 midpoint 0.000000
        comp_match = re.search(r'ComputationTime ([\d.]+)', line)
        total_match = re.search(r'TotalTime ([\d.]+)', line)
        if comp_match and total_match:
            return float(comp_match.group(1)), float(total_match.group(1))
    return None, None

# First, find max times per size for common y-axis scale
max_times = {}
for size in sizes:
    max_time = 0
    for nprocs in mpi_procs:
        mpi_file = os.path.join(mpi_results_dir, str(size), f'mpi_jacobi_constant_{nprocs}.out')
        comp_time, total_time = parse_mpi_result(mpi_file)
        if total_time and total_time > max_time:
            max_time = total_time
    max_times[size] = max_time * 1.35  # Add 35% margin for legend space

# Generate plots
os.makedirs(output_dir, exist_ok=True)

for size in sizes:
    for nprocs in mpi_procs:
        mpi_file = os.path.join(mpi_results_dir, str(size), f'mpi_jacobi_constant_{nprocs}.out')
        comp_time, total_time = parse_mpi_result(mpi_file)
        
        print(f"Size {size}, {nprocs} procs: Comp = {comp_time:.4f}s, Total = {total_time:.4f}s")
        
        # Create plot
        fig, ax = plt.subplots(figsize=(6, 6))
        
        x = np.array([0])
        width = 0.5
        
        # Stacked bar: Computation at bottom, remaining (Total - Comp) on top
        other_time = total_time - comp_time
        
        bar_comp = ax.bar(x, comp_time, width, label='Computation Time', color='#3498db')
        bar_other = ax.bar(x, other_time, width, bottom=comp_time, label='Other', color='#e74c3c')
        
        # Add total time label on top of bar
        ax.text(x, total_time + max_times[size]*0.02, f'{total_time:.3f}s', 
                ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # Add computation time label inside the bar
        ax.annotate(f'Comp: {comp_time:.3f}s', 
                    xy=(x, comp_time/2), 
                    xytext=(x + 0.35, comp_time/2),
                    fontsize=9, fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5),
                    va='center')
        
        # Add other time label inside if it's big enough
        if other_time > max_times[size] * 0.05:
            ax.text(x, comp_time + other_time/2, f'{other_time:.3f}s', 
                    ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        
        ax.set_xlabel('Method', fontsize=12)
        ax.set_ylabel('Seconds', fontsize=12)
        ax.set_title(f'Total vs Computation Time - Size = {size}, MPI Proc. = {nprocs}', fontsize=14, fontweight='bold')
        
        ax.set_xticks(x)
        ax.set_xticklabels(['Jacobi'], fontsize=11)
        
        # Common y-axis scale per size
        ax.set_ylim(0, max_times[size])
        
        ax.legend(loc='upper right', fontsize=10)
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save plot
        output_path = os.path.join(output_dir, f'time_comp_{size}_{nprocs}.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")
        
        plt.close()

print("\nAll plots generated successfully!")
