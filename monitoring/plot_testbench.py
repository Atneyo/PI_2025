from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


def _parse_time(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_power_w(sample: dict) -> float | None:
    energy = sample.get("energy", {}).get("energy", {})
    if not energy:
        return None
    # prefer total power
    v = energy.get("Total Power (W)")
    if v is None:
        v = energy.get("CPU Power (W)")
    return _to_float(v)


def _extract_ram_percent(sample: dict) -> float | None:
    mem = sample.get("memory", {})
    return _to_float(mem.get("ram_percent_used"))


def _extract_temp_c(sample: dict) -> float | None:
    temp = sample.get("temperature", {})
    # prefer CPU temp for graphs
    return _to_float(temp.get("cpu_temperature_c"))


def _collect_event_ranges(events: list[dict]) -> dict[str, list[tuple[datetime, datetime, int]]]:
    ranges: dict[str, list[tuple[datetime, datetime, int]]] = {"hailo": [], "cpu": []}
    open_events: dict[str, tuple[datetime, int] | None] = {"hailo": None, "cpu": None}
    for ev in events:
        ts = _parse_time(ev.get("timestamp"))
        if not ts:
            continue
        name = ev.get("event")
        idx = ev.get("run_index")
        if name == "hailo_run_start":
            open_events["hailo"] = (ts, idx)
        elif name == "hailo_run_end" and open_events["hailo"]:
            start_ts, run_index = open_events["hailo"]
            ranges["hailo"].append((start_ts, ts, run_index))
            open_events["hailo"] = None
        elif name == "cpu_run_start":
            open_events["cpu"] = (ts, idx)
        elif name == "cpu_run_end" and open_events["cpu"]:
            start_ts, run_index = open_events["cpu"]
            ranges["cpu"].append((start_ts, ts, run_index))
            open_events["cpu"] = None
    return ranges


def _split_series_by_ranges(
    times: list[datetime],
    values: list[float],
    ranges: list[tuple[datetime, datetime, int]],
):
    series: dict[int, list[tuple[datetime, float]]] = {}
    for t, v in zip(times, values):
        for start, end, run_index in ranges:
            if start <= t <= end:
                series.setdefault(run_index, []).append((t, v))
                break
    return series


def _plot_series(ax, series: dict[int, list[tuple[datetime, float]]], label_prefix: str):
    for run_index, points in sorted(series.items()):
        if not points:
            continue
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.plot(xs, ys, label=f"{label_prefix} run {run_index}")


def main():
    parser = argparse.ArgumentParser(description="Plot testbench monitoring graphs.")
    parser.add_argument(
        "--session",
        default="monitoring/testbench_outputs/testbench_hat_session.json",
        help="Path to testbench session JSON.",
    )
    parser.add_argument(
        "--out-dir",
        default="monitoring/testbench_outputs/plots",
        help="Output directory for plots.",
    )
    args = parser.parse_args()

    session_path = Path(args.session)
    if not session_path.exists():
        raise FileNotFoundError(f"Session file not found: {session_path}")

    session = json.loads(session_path.read_text(encoding="utf-8"))
    samples = session.get("monitoring_samples", [])
    events = session.get("events", [])

    times = []
    power = []
    ram = []
    temp = []
    for s in samples:
        ts = _parse_time(s.get("timestamp"))
        if not ts:
            continue
        p = _extract_power_w(s)
        r = _extract_ram_percent(s)
        t = _extract_temp_c(s)
        if p is None and r is None and t is None:
            continue
        times.append(ts)
        power.append(p)
        ram.append(r)
        temp.append(t)

    ranges = _collect_event_ranges(events)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    plots = [
        ("power_w", "Total Power (W)", power),
        ("ram_percent", "RAM % Used", ram),
        ("temp_c", "CPU Temp (C)", temp),
    ]

    for slug, y_label, values in plots:
        fig, ax = plt.subplots(figsize=(10, 4))

        hailo_series = _split_series_by_ranges(times, values, ranges["hailo"])
        cpu_series = _split_series_by_ranges(times, values, ranges["cpu"])

        _plot_series(ax, hailo_series, "HAT")
        _plot_series(ax, cpu_series, "CPU")

        ax.set_title(f"{y_label} vs Time")
        ax.set_xlabel("Time")
        ax.set_ylabel(y_label)
        ax.legend(loc="best")
        fig.autofmt_xdate()

        out_path = out_dir / f"{slug}_vs_time.png"
        fig.tight_layout()
        fig.savefig(out_path)
        plt.close(fig)

        print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
