#!/usr/bin/env python3
import re
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
PLOTS_DIR = BASE_DIR / "plots"

SEQ_FOLDER = "seq"
VERSIONS = {
    "naive": {"label": "Naive", "folder": "naive"},
    "transpose": {"label": "Transpose", "folder": "transpose"},
    "shared_mem": {"label": "Shared", "folder": "shared_mem"},
    "all_gpu": {"label": "All-GPU", "folder": "all_gpu"},
    "reduction": {"label": "Reduction", "folder": "reduction"},
    "all_gpu_all_reduction": {"label": "All-Reduction", "folder": "all_gpu_all_reduction"},
}

COORDS = [32, 2]
DISPLAY_BLOCKS = [32, 48, 64, 128, 256, 512, 1024]


def parse_float(pattern, text):
    match = re.search(pattern, text)
    if not match:
        return None
    return float(match.group(1))


def parse_timings(path):
    text = path.read_text()
    t_loop_avg = parse_float(r"t_loop_avg\s*=\s*([0-9.]+)\s*ms", text)
    t_cpu_avg = parse_float(r"t_cpu_avg\s*=\s*([0-9.]+)\s*ms", text)
    t_gpu_avg = parse_float(r"t_gpu_avg\s*=\s*([0-9.]+)\s*ms", text)
    t_transfers_avg = parse_float(r"t_transfers_avg\s*=\s*([0-9.]+)\s*ms", text)
    total = parse_float(r"total\s*=\s*([0-9.]+)\s*ms", text)
    nloops = parse_float(r"nloops\s*=\s*([0-9.]+)\s*:", text)
    if t_loop_avg is None and total is not None and nloops:
        t_loop_avg = total / nloops
    return {
        "loop": t_loop_avg,
        "cpu": t_cpu_avg,
        "gpu": t_gpu_avg,
        "transfers": t_transfers_avg,
    }


def parse_filename(path):
    coords_match = re.search(r"Coo-(\d+)", path.name)
    block_match = re.search(r"Bs-(\d+)", path.name)
    coords = int(coords_match.group(1)) if coords_match else None
    block_size = int(block_match.group(1)) if block_match else None
    return coords, block_size


def load_seq_times():
    seq_times = {}
    seq_dir = BASE_DIR / SEQ_FOLDER
    for path in seq_dir.glob("*.out"):
        coords, _ = parse_filename(path)
        if coords is None:
            continue
        timings = parse_timings(path)
        if timings["loop"] is not None:
            seq_times[coords] = timings["loop"]
    return seq_times


def load_version_data():
    data = {version: {} for version in VERSIONS}
    for version, meta in VERSIONS.items():
        folder = BASE_DIR / meta["folder"]
        if not folder.exists():
            continue
        for path in folder.glob("*.out"):
            coords, block_size = parse_filename(path)
            if coords is None or block_size is None:
                continue
            timings = parse_timings(path)
            if timings["loop"] is None:
                continue
            data[version].setdefault(coords, {})[block_size] = timings
    return data


def plot_stacked_bar(version, coords, seq_time, data, out_dir):
    plot_stacked_bar_internal(version, coords, seq_time, data, out_dir, include_sequential=True)


def plot_stacked_bar_gpu_only(version, coords, data, out_dir):
    plot_stacked_bar_internal(version, coords, None, data, out_dir, include_sequential=False)


def plot_stacked_bar_internal(version, coords, seq_time, data, out_dir, include_sequential):
    label = VERSIONS[version]["label"]
    blocks = sorted(data.get(coords, {}).keys())
    if not blocks:
        return
    if include_sequential:
        x_labels = ["sequential"] + [str(b) for b in DISPLAY_BLOCKS]
        gpu = [0.0]
        transfers = [0.0]
        cpu = [seq_time]
    else:
        x_labels = [str(b) for b in DISPLAY_BLOCKS]
        gpu = []
        transfers = []
        cpu = []
    for block in DISPLAY_BLOCKS:
        timings = data[coords].get(block)
        gpu.append((timings or {}).get("gpu") or 0.0)
        transfers.append((timings or {}).get("transfers") or 0.0)
        cpu.append((timings or {}).get("cpu") or 0.0)

    x = list(range(len(x_labels)))
    plt.figure(figsize=(11, 5))
    bar_width = 0.5
    plt.bar(x, gpu, width=bar_width, label="GPU time", color="#1f77b4")
    plt.bar(x, transfers, width=bar_width, bottom=gpu, label="Transfer time", color="#ff7f0e")
    bottom = [g + t for g, t in zip(gpu, transfers)]
    plt.bar(x, cpu, width=bar_width, bottom=bottom, label="CPU time", color="#2ca02c")
    plt.xticks(x, x_labels)
    plt.xlabel("Configuration")
    plt.ylabel("Time (ms)")
    if include_sequential:
        title_suffix = "Execution Time"
    else:
        title_suffix = "Execution Time (GPU-only)"
    plt.title(f"{label} {title_suffix} (coords={coords})")
    max_total = max((g + t + c for g, t, c in zip(gpu, transfers, cpu)), default=0.0)
    if max_total > 0.0:
        plt.ylim(0.0, max_total * 1.1)
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    if include_sequential:
        out_name = f"bar_{version}_coords{coords}.png"
    else:
        out_name = f"bar_{version}_coords{coords}_gpu_only.png"
    out_path = out_dir / out_name
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_metric_bars(version, coords, data, out_dir):
    label = VERSIONS[version]["label"]
    version_data = data.get(coords, {})
    blocks = sorted(version_data.keys())
    if not blocks:
        return
    metrics = [
        ("gpu", "GPU time"),
        ("transfers", "Transfer time"),
        ("cpu", "CPU time"),
        ("loop", "Total loop time"),
    ]
    for metric_key, metric_label in metrics:
        values = [(version_data.get(b) or {}).get(metric_key) or 0.0 for b in DISPLAY_BLOCKS]
        plt.figure(figsize=(8, 4.5))
        bar_width = 0.5
        x = list(range(len(DISPLAY_BLOCKS)))
        bars = plt.bar(x, values, width=bar_width, color="#1f77b4")
        plt.xticks(x, [str(b) for b in DISPLAY_BLOCKS])
        plt.xlabel("Block size")
        plt.ylabel("Time (ms)")
        plt.title(f"{label} {metric_label} (coords={coords})")
        max_value = max(values) if values else 0.0
        if max_value > 0.0:
            plt.ylim(0.0, max_value * 1.1)
        plt.grid(axis="y", alpha=0.3)
        if metric_key == "transfers":
            annotate_bar_values(bars, values)
        plt.tight_layout()
        out_path = out_dir / f"coords{coords}_metric_{metric_key}.png"
        plt.savefig(out_path, dpi=200)
        plt.close()
        if metric_key == "transfers":
            plot_transfer_deltas(label, coords, values, out_dir)


def annotate_speedups(x_vals, speedups):
    if not speedups:
        return
    max_val = max(speedups)
    offset = max(0.02, max_val * 0.02)
    for x_val, speedup in zip(x_vals, speedups):
        plt.text(
            x_val,
            speedup + offset,
            f"{speedup:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )


def annotate_bar_values(bars, values):
    max_value = max(values) if values else 0.0
    offset = max(0.02, max_value * 0.02)
    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            value + offset,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=7,
            fontweight="bold",
            rotation=90,
        )


def plot_transfer_deltas(label, coords, values, out_dir):
    if not values:
        return
    min_value = min(values)
    deltas = [v - min_value for v in values]
    plt.figure(figsize=(8, 4.5))
    bar_width = 0.5
    x = list(range(len(DISPLAY_BLOCKS)))
    plt.bar(x, deltas, width=bar_width, color="#9467bd")
    plt.xticks(x, [str(b) for b in DISPLAY_BLOCKS])
    plt.xlabel("Block size")
    plt.ylabel("Delta vs min (ms)")
    plt.title(f"{label} Transfer Delta (coords={coords})")
    max_delta = max(deltas) if deltas else 0.0
    if max_delta > 0.0:
        plt.ylim(0.0, max_delta * 1.1)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    out_path = out_dir / f"coords{coords}_metric_transfers_delta.png"
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_speedup_single(version, coords, seq_time, data, out_dir):
    label = VERSIONS[version]["label"]
    version_data = data.get(coords, {})
    blocks = sorted(version_data.keys())
    if not blocks:
        return
    speedups = [seq_time / version_data[b]["loop"] for b in blocks]
    x_positions = {block: idx for idx, block in enumerate(DISPLAY_BLOCKS)}
    x_vals = [x_positions[b] for b in blocks if b in x_positions]
    speedups = [speedups[i] for i, b in enumerate(blocks) if b in x_positions]
    plt.figure(figsize=(8, 5))
    plt.plot(x_vals, speedups, marker="o", label=label)
    plt.xlabel("Block size")
    plt.ylabel("Speedup (seq_time / time)")
    plt.title(f"{label} Speedup (coords={coords})")
    plt.axhline(1.0, linestyle=":", color="gray", linewidth=1)
    annotate_speedups(x_vals, speedups)
    plt.xticks(list(range(len(DISPLAY_BLOCKS))), [str(b) for b in DISPLAY_BLOCKS])
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    out_path = out_dir / f"coords{coords}_speedup.png"
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_speedup(plot_name, coords, seq_time, data, versions, annotate_last_only=True):
    plt.figure(figsize=(8, 5))
    x_positions = {block: idx for idx, block in enumerate(DISPLAY_BLOCKS)}
    plotted = False
    annotate_version = versions[-1] if versions and annotate_last_only else None
    for version in versions:
        version_data = data.get(version, {}).get(coords, {})
        if not version_data:
            continue
        blocks = sorted(version_data.keys())
        speedups = [seq_time / version_data[b]["loop"] for b in blocks]
        x_vals = [x_positions[b] for b in blocks if b in x_positions]
        speedups = [speedups[i] for i, b in enumerate(blocks) if b in x_positions]
        label = VERSIONS[version]["label"]
        plt.plot(x_vals, speedups, marker="o", label=label)
        if annotate_version is None or version == annotate_version:
            annotate_speedups(x_vals, speedups)
        plotted = True
    if not plotted:
        plt.close()
        return
    plt.xlabel("Block size")
    plt.ylabel("Speedup (seq_time / time)")
    plt.title(f"Speedup (coords={coords})")
    plt.axhline(1.0, linestyle=":", color="gray", linewidth=1)
    plt.xticks(list(range(len(DISPLAY_BLOCKS))), [str(b) for b in DISPLAY_BLOCKS])
    plt.grid(axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    out_path = PLOTS_DIR / f"{plot_name}_coords{coords}.png"
    plt.savefig(out_path, dpi=200)
    plt.close()


def main():
    PLOTS_DIR.mkdir(exist_ok=True)
    seq_times = load_seq_times()
    data = load_version_data()

    for coords in COORDS:
        if coords not in seq_times:
            continue
        seq_time = seq_times[coords]
        for version in VERSIONS:
            version_dir = BASE_DIR / VERSIONS[version]["folder"]
            version_plots = version_dir / "plots"
            version_plots.mkdir(exist_ok=True)
            plot_stacked_bar(version, coords, seq_time, data.get(version, {}), PLOTS_DIR)
            plot_stacked_bar(version, coords, seq_time, data.get(version, {}), version_plots)
            plot_stacked_bar_gpu_only(version, coords, data.get(version, {}), PLOTS_DIR)
            plot_stacked_bar_gpu_only(version, coords, data.get(version, {}), version_plots)
            plot_metric_bars(version, coords, data.get(version, {}), version_plots)
            plot_speedup_single(version, coords, seq_time, data.get(version, {}), version_plots)

        plot_speedup("speedup_naive", coords, seq_time, data, ["naive"])
        plot_speedup("speedup_naive_transpose", coords, seq_time, data, ["naive", "transpose"])
        plot_speedup(
            "speedup_naive_transpose_shared",
            coords,
            seq_time,
            data,
            ["naive", "transpose", "shared_mem"],
        )
        plot_speedup(
            "speedup_naive_transpose_shared_all_gpu",
            coords,
            seq_time,
            data,
            ["naive", "transpose", "shared_mem", "all_gpu"],
        )
        plot_speedup(
            "speedup_all_versions",
            coords,
            seq_time,
            data,
            ["naive", "transpose", "shared_mem", "all_gpu", "reduction", "all_gpu_all_reduction"],
        )


if __name__ == "__main__":
    main()
