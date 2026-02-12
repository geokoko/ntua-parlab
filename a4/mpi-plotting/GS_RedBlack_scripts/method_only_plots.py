#!/usr/bin/env python3
"""
Single-method MPI plots for Gauss-Seidel SOR and Red-Black SOR.
Outputs to plots/gauss_seidel_only and plots/red_black_only.
"""

import re
from pathlib import Path
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

ROOT = Path(__file__).resolve().parent
PROJECT = (ROOT / '..' / 'heat_transfer').resolve()
OUTPUT_DIR = ROOT / 'plots'

METHODS = {
    "GaussSeidelSOR": {
        "label": "Gauss-Seidel SOR",
        "color": "#e74c3c",
        "subdir": "gauss_seidel_only",
    },
    "RedBlackSOR": {
        "label": "Red-Black SOR",
        "color": "#2ecc71",
        "subdir": "red_black_only",
    },
}

SIZES = [2048, 4096, 6144]
PROCS = [1, 2, 4, 8, 16, 32, 64]
BAR_PROCS = [8, 16, 32, 64]

KEYS = {
    "X",
    "Y",
    "Px",
    "Py",
    "Iter",
    "ComputationTime",
    "TotalTime",
    "CommunicationTime",
    "ConvergenceTime",
}


def parse_line(line: str):
    tokens = line.strip().split()
    if not tokens:
        return None
    method = tokens[0]
    kv = {}
    i = 1
    while i < len(tokens) - 1:
        key = tokens[i]
        if key in KEYS:
            kv[key] = tokens[i + 1]
            i += 2
        else:
            i += 1
    if "X" not in kv or "Y" not in kv:
        return None
    try:
        return {
            "method": method,
            "X": int(kv["X"]),
            "Y": int(kv["Y"]),
            "Px": int(kv.get("Px", 1)),
            "Py": int(kv.get("Py", 1)),
            "Iter": int(kv.get("Iter", 0)),
            "ComputationTime": float(kv.get("ComputationTime", "nan")),
            "TotalTime": float(kv.get("TotalTime", "nan")),
            "CommunicationTime": float(kv.get("CommunicationTime", "nan")),
            "ConvergenceTime": float(kv.get("ConvergenceTime", "nan")),
        }
    except ValueError:
        return None


def load_gauss_constant():
    data = []
    path = PROJECT / 'gauss_seidel' / 'mpi' / 'results' / 'gauss_heat_transfer_mpi.out'
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        rec = parse_line(line)
        if rec is None:
            continue
        if rec["Iter"] != 256:
            continue
        data.append(rec)
    return data


def load_red_black_constant():
    data = []
    base = PROJECT / 'red_black' / 'mpi' / 'rb_results'
    for path in base.glob('const_*/*.out'):
        lines = path.read_text().splitlines()
        if not lines:
            continue
        rec = parse_line(lines[0])
        if rec is None:
            continue
        if rec["Iter"] != 256:
            continue
        data.append(rec)
    return data


def build_averages(records):
    buckets = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for rec in records:
        method = rec["method"]
        size = rec["X"]
        p = rec["Px"] * rec["Py"]
        buckets[method][size][p].append(rec)

    averages = defaultdict(lambda: defaultdict(dict))
    for method, sizes in buckets.items():
        for size, procs in sizes.items():
            for p, items in procs.items():
                comp = np.mean([r["ComputationTime"] for r in items])
                total = np.mean([r["TotalTime"] for r in items])
                averages[method][size][p] = {
                    "comp": float(comp),
                    "total": float(total),
                    "n": len(items),
                }
    return averages


def plot_speedup(method, averages):
    label = METHODS[method]["label"]
    color = METHODS[method]["color"]
    out_dir = OUTPUT_DIR / METHODS[method]["subdir"]

    for size in SIZES:
        base = averages.get(method, {}).get(size, {}).get(1)
        if not base:
            print(f"Missing p=1 for {label} size {size}, skipping.")
            continue
        base_total = base["total"]

        speedups = []
        xs = []
        for p in PROCS:
            entry = averages.get(method, {}).get(size, {}).get(p)
            if not entry:
                continue
            xs.append(p)
            speedups.append(base_total / entry["total"])

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(xs, speedups, 'o-', linewidth=2, markersize=8, label=label, color=color)

        ax.set_xlabel('MPI Processes', fontsize=12)
        ax.set_ylabel('Speedup', fontsize=12)
        ax.set_title(f'Speedup for Grid {size}x{size}', fontsize=14, fontweight='bold')

        ax.set_xticks(PROCS)
        ax.set_xticklabels([str(p) for p in PROCS])

        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)

        plt.tight_layout()
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f'speedup_{size}.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")
        plt.close()


def plot_time_comp(method, averages):
    label = METHODS[method]["label"]
    out_dir = OUTPUT_DIR / METHODS[method]["subdir"]

    # Compute max times per size for common y-axis scale
    max_times = {}
    for size in SIZES:
        max_time = 0.0
        for nprocs in BAR_PROCS:
            entry = averages.get(method, {}).get(size, {}).get(nprocs)
            if not entry:
                continue
            max_time = max(max_time, entry["total"])
        max_times[size] = max_time * 1.35 if max_time > 0 else 0.0

    for size in SIZES:
        if max_times[size] <= 0:
            continue
        for nprocs in BAR_PROCS:
            entry = averages.get(method, {}).get(size, {}).get(nprocs)
            if not entry:
                continue
            comp_time = entry["comp"]
            total_time = entry["total"]
            other_time = total_time - comp_time

            fig, ax = plt.subplots(figsize=(6, 6))

            x = np.array([0])
            width = 0.5

            ax.bar(x, comp_time, width, label='Computation Time', color='#3498db')
            ax.bar(x, other_time, width, bottom=comp_time, label='Other', color='#e74c3c')

            ax.text(x, total_time + max_times[size] * 0.02, f'{total_time:.3f}s',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

            ax.annotate(f'Comp: {comp_time:.3f}s',
                        xy=(x, comp_time/2),
                        xytext=(x + 0.35, comp_time/2),
                        fontsize=9, fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5),
                        va='center')

            if other_time > max_times[size] * 0.05:
                ax.text(x, comp_time + other_time/2, f'{other_time:.3f}s',
                        ha='center', va='center', fontsize=9, color='white', fontweight='bold')

            ax.set_xlabel('Method', fontsize=12)
            ax.set_ylabel('Seconds', fontsize=12)
            ax.set_title(
                f'Total vs Computation Time - Size = {size}, MPI Proc. = {nprocs}',
                fontsize=14,
                fontweight='bold',
            )

            ax.set_xticks(x)
            ax.set_xticklabels([label], fontsize=11)
            ax.set_ylim(0, max_times[size])

            ax.legend(loc='upper right', fontsize=10)
            ax.yaxis.grid(True, linestyle='--', alpha=0.7)
            ax.set_axisbelow(True)

            plt.tight_layout()
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = out_dir / f'time_comp_{size}_{nprocs}.png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {output_path}")
            plt.close()


def load_converge(method):
    if method == "GaussSeidelSOR":
        gs_path = PROJECT / 'gauss_seidel' / 'mpi' / 'results' / 'gauss_heat_transfer_mpi_CONV.out'
        if not gs_path.exists():
            return None
        line = gs_path.read_text().strip()
        rec = parse_line(line)
        if not rec:
            return None
        return rec["ComputationTime"], rec.get("ConvergenceTime", 0.0), rec["TotalTime"]

    if method == "RedBlackSOR":
        rb_base = PROJECT / 'red_black' / 'mpi' / 'rb_results' / 'conv_512'
        if not rb_base.exists():
            return None
        records = []
        for path in rb_base.glob('*.out'):
            lines = path.read_text().splitlines()
            if not lines:
                continue
            rec = parse_line(lines[0])
            if rec:
                records.append(rec)
        if not records:
            return None
        comp = np.mean([r["ComputationTime"] for r in records])
        conv = np.mean([r.get("ConvergenceTime", 0.0) for r in records])
        total = np.mean([r["TotalTime"] for r in records])
        return float(comp), float(conv), float(total)

    return None


def plot_converge(method):
    label = METHODS[method]["label"]
    out_dir = OUTPUT_DIR / METHODS[method]["subdir"]

    data = load_converge(method)
    if data is None:
        print(f"Missing converge data for {label}.")
        return

    comp_time, conv_time, total_time = data
    other_time = total_time - comp_time - conv_time

    fig, ax = plt.subplots(figsize=(8, 6))

    x = np.array([0])
    width = 0.5

    ax.bar(x, comp_time, width, label='Computation Time', color='#3498db')
    ax.bar(x, conv_time, width, bottom=comp_time, label='Converge Time', color='#e74c3c')
    ax.bar(x, other_time, width, bottom=comp_time + conv_time, label='Other', color='#f39c12')

    ax.text(x[0], total_time + total_time * 0.05, f'{total_time:.2f}s',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('Time (seconds)', fontsize=12)
    ax.set_title('With Converge (512x512, 64 MPI Processes)',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([label], fontsize=11)

    ax.legend(loc='upper right', fontsize=10)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_ylim(0, total_time * 1.1)

    plt.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / 'converge_512_p64.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    plt.close()


def main():
    records = []
    records.extend(load_gauss_constant())
    records.extend(load_red_black_constant())
    averages = build_averages(records)

    for method in METHODS:
        plot_speedup(method, averages)
        plot_time_comp(method, averages)
        plot_converge(method)


if __name__ == '__main__':
    main()
