#!/usr/bin/env python3

import re
from pathlib import Path
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
PROJECT = (ROOT / ".." / "heat_transfer").resolve()
OUTPUT_DIR = ROOT / "plots" / "comparisons"

METHODS = {
    "Jacobi": {"label": "Jacobi", "color": "#3498db"},
    "GaussSeidelSOR": {"label": "Gauss-Seidel SOR", "color": "#e74c3c"},
    "RedBlackSOR": {"label": "Red-Black SOR", "color": "#2ecc71"},
}
METHOD_ORDER = ["Jacobi", "GaussSeidelSOR", "RedBlackSOR"]

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


def load_jacobi_constant():
    data = []
    base = PROJECT / "jacobi" / "mpi" / "jac_results"
    for path in base.glob("*/mpi_jacobi_constant_*.out"):
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


def load_gauss_constant():
    data = []
    path = PROJECT / "gauss_seidel" / "mpi" / "results" / "gauss_heat_transfer_mpi.out"
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
    base = PROJECT / "red_black" / "mpi" / "rb_results"
    for path in base.glob("const_*/*.out"):
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


def warn_missing(averages):
    for method in METHOD_ORDER:
        for size in SIZES:
            for p in PROCS:
                if p not in averages.get(method, {}).get(size, {}):
                    print(f"warning: missing {method} size {size} p {p}")


def plot_speedup(averages):
    for size in SIZES:
        fig, ax = plt.subplots(figsize=(8, 6))
        for method in METHOD_ORDER:
            if size not in averages.get(method, {}):
                continue
            base = averages[method][size].get(1)
            if not base:
                continue
            base_total = base["total"]
            speedups = []
            xs = []
            for p in PROCS:
                entry = averages[method][size].get(p)
                if not entry:
                    continue
                xs.append(p)
                speedups.append(base_total / entry["total"])
            if xs:
                ax.plot(
                    xs,
                    speedups,
                    'o-',
                    linewidth=2,
                    markersize=8,
                    label=METHODS[method]["label"],
                    color=METHODS[method]["color"],
                )

        ax.set_xlabel('MPI Processes', fontsize=12)
        ax.set_ylabel('Speedup', fontsize=12)
        ax.set_title(f'Speedup for Grid {size}x{size}', fontsize=14, fontweight='bold')
        ax.set_xticks(PROCS)
        ax.set_xticklabels([str(p) for p in PROCS])
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)

        plt.tight_layout()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"compare_speedup_{size}.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")
        plt.close()


def plot_time_comp(averages):
    # Compute max times per size for common y-axis scale
    max_times = {}
    for size in SIZES:
        max_time = 0.0
        for nprocs in BAR_PROCS:
            for method in METHOD_ORDER:
                entry = averages.get(method, {}).get(size, {}).get(nprocs)
                if not entry:
                    continue
                max_time = max(max_time, entry["total"])
        max_times[size] = max_time * 1.35 if max_time > 0 else 0.0

    for size in SIZES:
        if max_times[size] <= 0:
            continue

        for nprocs in BAR_PROCS:
            comp_times = []
            other_times = []
            total_times = []

            for method in METHOD_ORDER:
                entry = averages.get(method, {}).get(size, {}).get(nprocs)
                if not entry:
                    comp_times.append(float('nan'))
                    other_times.append(float('nan'))
                    total_times.append(float('nan'))
                    continue
                comp = entry["comp"]
                total = entry["total"]
                other = max(total - comp, 0.0)
                comp_times.append(comp)
                other_times.append(other)
                total_times.append(total)

            fig, ax = plt.subplots(figsize=(6, 6))

            x = np.arange(len(METHOD_ORDER))
            width = 0.6

            ax.bar(x, comp_times, width, label='Computation Time', color='#3498db')
            ax.bar(x, other_times, width, bottom=comp_times, label='Other', color='#e74c3c')

            # Total labels above bars
            for i, total in enumerate(total_times):
                if not np.isfinite(total):
                    continue
                ax.text(x[i], total + max_times[size] * 0.02, f'{total:.3f}s',
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

            # Optional labels inside bars if large enough
            for i, (comp, other) in enumerate(zip(comp_times, other_times)):
                if not np.isfinite(comp) or not np.isfinite(other):
                    continue
                if comp > max_times[size] * 0.05:
                    ax.text(x[i], comp / 2, f'{comp:.3f}s',
                            ha='center', va='center', fontsize=9, color='white', fontweight='bold')
                if other > max_times[size] * 0.05:
                    ax.text(x[i], comp + other / 2, f'{other:.3f}s',
                            ha='center', va='center', fontsize=9, color='white', fontweight='bold')

            ax.set_xlabel('Method', fontsize=12)
            ax.set_ylabel('Seconds', fontsize=12)
            ax.set_title(
                f'Total vs Computation Time - Size = {size}, MPI Proc. = {nprocs}',
                fontsize=14,
                fontweight='bold',
            )

            ax.set_xticks(x)
            ax.set_xticklabels([METHODS[m]["label"] for m in METHOD_ORDER], fontsize=11)
            ax.set_ylim(0, max_times[size])

            ax.legend(loc='upper right', fontsize=10)
            ax.yaxis.grid(True, linestyle='--', alpha=0.7)
            ax.set_axisbelow(True)

            plt.tight_layout()
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_path = OUTPUT_DIR / f"compare_time_comp_{size}_{nprocs}.png"
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {output_path}")
            plt.close()


def load_converge_results():
    results = {}

    # Jacobi converge
    jac_path = PROJECT / "jacobi" / "mpi" / "jac_results" / "mpi_jacobi_converge.out"
    if jac_path.exists():
        lines = jac_path.read_text().splitlines()
        if lines:
            rec = parse_line(lines[0])
            conv_time = 0.0
            for line in lines[1:]:
                match = re.search(r'Total converge time\s+([\d.]+)', line)
                if match:
                    conv_time = float(match.group(1))
                    break
            if rec:
                results["Jacobi"] = {
                    "comp": rec["ComputationTime"],
                    "total": rec["TotalTime"],
                    "conv": conv_time,
                }

    # Gauss-Seidel converge
    gs_path = PROJECT / "gauss_seidel" / "mpi" / "results" / "gauss_heat_transfer_mpi_CONV.out"
    if gs_path.exists():
        line = gs_path.read_text().strip()
        if line:
            rec = parse_line(line)
            if rec:
                results["GaussSeidelSOR"] = {
                    "comp": rec["ComputationTime"],
                    "total": rec["TotalTime"],
                    "conv": rec.get("ConvergenceTime", 0.0),
                }

    # Red-Black converge (average multiple runs)
    rb_base = PROJECT / "red_black" / "mpi" / "rb_results" / "conv_512"
    rb_records = []
    if rb_base.exists():
        for path in rb_base.glob("*.out"):
            lines = path.read_text().splitlines()
            if not lines:
                continue
            rec = parse_line(lines[0])
            if rec:
                rb_records.append(rec)
        if rb_records:
            comp = np.mean([r["ComputationTime"] for r in rb_records])
            total = np.mean([r["TotalTime"] for r in rb_records])
            conv = np.mean([r.get("ConvergenceTime", 0.0) for r in rb_records])
            results["RedBlackSOR"] = {
                "comp": float(comp),
                "total": float(total),
                "conv": float(conv),
            }

    return results


def plot_converge(results):
    if not results:
        return

    fig, ax = plt.subplots(figsize=(10, 7))

    x = np.arange(len(METHOD_ORDER))
    width = 0.5

    comp_vals = []
    conv_vals = []
    other_vals = []
    total_vals = []

    for method in METHOD_ORDER:
        entry = results.get(method)
        if not entry:
            comp_vals.append(float('nan'))
            conv_vals.append(float('nan'))
            other_vals.append(float('nan'))
            total_vals.append(float('nan'))
            continue
        comp = entry["comp"]
        conv = entry["conv"]
        total = entry["total"]
        other = max(total - comp - conv, 0.0)
        comp_vals.append(comp)
        conv_vals.append(conv)
        other_vals.append(other)
        total_vals.append(total)

    ax.bar(x, comp_vals, width, label='Computation Time', color='#3498db')
    ax.bar(x, conv_vals, width, bottom=comp_vals, label='Converge Time', color='#e74c3c')
    ax.bar(
        x,
        other_vals,
        width,
        bottom=(np.array(comp_vals) + np.array(conv_vals)),
        label='Other',
        color='#f39c12',
    )

    max_total = max([t for t in total_vals if np.isfinite(t)], default=0.0)
    ylimit = max_total * 1.1 if max_total > 0 else 1.0

    for i, total in enumerate(total_vals):
        if not np.isfinite(total):
            continue
        ax.text(x[i], total + ylimit * 0.03, f'{total:.2f}s',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('Time (seconds)', fontsize=12)
    ax.set_title('With Converge (512x512, 64 MPI Processes)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([METHODS[m]["label"] for m in METHOD_ORDER], fontsize=11)

    ax.legend(loc='upper right', fontsize=10)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_ylim(0, ylimit)

    plt.tight_layout()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / 'compare_converge_512_p64.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    plt.close()


def main():
    records = []
    records.extend(load_jacobi_constant())
    records.extend(load_gauss_constant())
    records.extend(load_red_black_constant())
    averages = build_averages(records)
    warn_missing(averages)

    plot_speedup(averages)
    plot_time_comp(averages)

    converge_results = load_converge_results()
    plot_converge(converge_results)


if __name__ == "__main__":
    main()
