#!/usr/bin/env python3
"""
Σύγκριση χρόνων εκτέλεσης Serial vs MPI Jacobi (512x512, 64 MPI processes)
"""

import matplotlib.pyplot as plt
import numpy as np
import os

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

# Δεδομένα από τα αρχεία αποτελεσμάτων
# Serial: Jacobi X 512 Y 512 Iter 236000 Time 398.283326
serial_total_time = 398.283326

# MPI (8x8 = 64 processes): 
# ComputationTime 3.245958 TotalTime 58.559781
# Total converge time 1.768302
mpi_computation_time = 3.245958
mpi_converge_time = 1.768302
mpi_total_time = 58.559781

# Υπολογισμός του υπόλοιπου χρόνου (communication/overhead)
mpi_other_time = mpi_total_time - mpi_computation_time - mpi_converge_time

# Δημιουργία του plot
fig, ax = plt.subplots(figsize=(10, 7))

# Θέσεις των bars
x = np.array([0, 1])
width = 0.5

# Serial bar (μόνο total time)
serial_bar = ax.bar(x[0], serial_total_time, width, label='Total Time', color='#2ecc71')

# MPI stacked bar
# Από κάτω προς τα πάνω: Computation -> Converge -> Other (για το total)
mpi_computation = ax.bar(x[1], mpi_computation_time, width, 
                          label='Computation Time', color='#3498db')
mpi_converge = ax.bar(x[1], mpi_converge_time, width, 
                       bottom=mpi_computation_time,
                       label='Converge Time', color='#e74c3c')
mpi_other = ax.bar(x[1], mpi_other_time, width, 
                    bottom=mpi_computation_time + mpi_converge_time,
                    label='Other', color='#f39c12')

# Προσθήκη τιμών πάνω από τα bars
ax.text(x[0], serial_total_time + 5, f'{serial_total_time:.2f}s', 
        ha='center', va='bottom', fontsize=11, fontweight='bold')
ax.text(x[1], mpi_total_time + 5, f'{mpi_total_time:.2f}s', 
        ha='center', va='bottom', fontsize=11, fontweight='bold')

# Προσθήκη τιμών μέσα στα stacked segments του MPI
# Computation και Converge είναι μικρά, βάζουμε labels στο πλάι με βέλη
ax.annotate(f'Comp: {mpi_computation_time:.2f}s', 
            xy=(x[1], mpi_computation_time/2), 
            xytext=(x[1] + 0.35, mpi_computation_time/2),
            fontsize=9, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5),
            va='center')
ax.annotate(f'Conv: {mpi_converge_time:.2f}s', 
            xy=(x[1], mpi_computation_time + mpi_converge_time/2), 
            xytext=(x[1] + 0.35, mpi_computation_time + mpi_converge_time/2 + 3),
            fontsize=9, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.5),
            va='center')
ax.text(x[1], mpi_computation_time + mpi_converge_time + mpi_other_time/2, 
        f'{mpi_other_time:.2f}s', 
        ha='center', va='center', fontsize=9, color='white', fontweight='bold')

# Ρυθμίσεις αξόνων
ax.set_ylabel('Time (seconds)', fontsize=12)
ax.set_title('With Converge (Serial vs 64 MPI Processes)', 
             fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(['Serial', 'Jacobi'], fontsize=11)

# Υπόμνημα
ax.legend(loc='upper right', fontsize=10)

# Προσθήκη grid για καλύτερη αναγνωσιμότητα
ax.yaxis.grid(True, linestyle='--', alpha=0.7)
ax.set_axisbelow(True)

# Ρύθμιση ορίων y-axis
ax.set_ylim(0, serial_total_time * 1.1)

plt.tight_layout()

# Αποθήκευση του plot
output_dir = os.path.join(os.path.dirname(__file__), 'plots')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'converge.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Plot saved to: {output_path}")
