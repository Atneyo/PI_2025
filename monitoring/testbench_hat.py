from __future__ import annotations

import argparse
import datetime
import json
import threading
import time
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from monitoring.detect_camera import get_cur_camera_presence
from monitoring.detect_hailo import get_cur_hailo_presence, is_hailo_hat_present
from monitoring.energy_monitoring import (
    start_energy_monitoring,
    stop_energy_monitoring,
    get_energy_info,
    get_energy_data_for_cur_log,
    JSON_FILE as ENERGY_JSON_FILE,
)
from monitoring.temperature_monitoring import (
    get_temp_info,
    get_temp_data_for_cur_log,
    file as TEMP_LOG_FILE,
)
from monitoring.memory_monitoring import (
    get_disk_info,
    get_memory_info,
    current_mem_disk_stats,
)
from monitoring.global_monitoring_functions import (
    save_cur_stats_json,
    save_to_json,
    glob_filename,
    glob_interval,
)

from interface.backend.AI.yolo_detection import yolo_detection
from interface.backend.AI.yolo_detection_without_yolo import yolo_detection_without_yolo


CAMERA_LOG_FILE = "camera_log.json"
HAILO_LOG_FILE = "hailo_log.json"


def _monitoring_loop(
    stop_event: threading.Event,
    interval: int,
    summary: dict,
    summary_path: Path,
    lock: threading.Lock,
):
    while not stop_event.is_set():
        sample = {"timestamp": datetime.datetime.now().isoformat()}
        # energy
        energy_info = get_energy_info()
        if energy_info:
            save_to_json(ENERGY_JSON_FILE, energy_info)
            save_cur_stats_json(glob_filename, get_energy_data_for_cur_log(energy_info))
            sample["energy"] = energy_info

        # camera
        cam_presence = get_cur_camera_presence()
        save_to_json(CAMERA_LOG_FILE, cam_presence)
        save_cur_stats_json(glob_filename, cam_presence)
        sample["camera"] = cam_presence

        # hailo
        hailo_presence = get_cur_hailo_presence()
        save_to_json(HAILO_LOG_FILE, hailo_presence)
        save_cur_stats_json(glob_filename, hailo_presence)
        sample["hailo"] = hailo_presence

        # temperature
        temp_data = get_temp_info()
        if temp_data:
            save_to_json(TEMP_LOG_FILE, temp_data)
            save_cur_stats_json(glob_filename, get_temp_data_for_cur_log(temp_data))
            sample["temperature"] = temp_data

        # memory
        disk_data = get_disk_info()
        mem_data = get_memory_info()
        if disk_data and mem_data:
            save_to_json(
                "disk_log.json",
                {"timestamp": datetime.datetime.now().isoformat(), "disks": disk_data},
            )
            save_to_json("memory_log.json", mem_data)
            save_cur_stats_json(
                glob_filename,
                current_mem_disk_stats(mem_data, disk_data),
            )
            sample["disk"] = disk_data
            sample["memory"] = mem_data

        with lock:
            summary.setdefault("monitoring_samples", []).append(sample)
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        stop_event.wait(interval)


def _run_hailo(video_path: Path, output_dir: Path, run_index: int) -> dict:
    started_at = datetime.datetime.now().isoformat()
    try:
        output = yolo_detection(
            live_input=False,
            video_path=video_path,
            output_dir=output_dir,
            record_filename=f"hailo_run_{run_index}.mp4",
            frame_rate=5,
        )
        if isinstance(output, tuple):
            output_path = output[0]
        else:
            output_path = output
        ended_at = datetime.datetime.now().isoformat()
        return {
            "started_at": started_at,
            "ended_at": ended_at,
            "output_video": str(output_path),
            "summary_json": str(output_path.with_suffix(".json")),
        }
    except Exception as exc:
        ended_at = datetime.datetime.now().isoformat()
        return {
            "started_at": started_at,
            "ended_at": ended_at,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _run_cpu(video_path: Path, output_dir: Path, yolo_path: Path | None, run_index: int) -> dict:
    started_at = datetime.datetime.now().isoformat()
    try:
        output, stats = yolo_detection_without_yolo(
            live_input=False,
            video_path=video_path,
            output_dir=output_dir,
            record_filename=f"cpu_run_{run_index}.mp4",
            frame_rate=5,
            yolo_path=yolo_path,
        )
        ended_at = datetime.datetime.now().isoformat()
        return {
            "started_at": started_at,
            "ended_at": ended_at,
            "output_video": str(output),
            "summary_json": str(output.with_suffix(".json")),
            "stats": stats,
        }
    except Exception as exc:
        ended_at = datetime.datetime.now().isoformat()
        return {
            "started_at": started_at,
            "ended_at": ended_at,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main():
    parser = argparse.ArgumentParser(description="HAT testbench with monitoring.")
    parser.add_argument(
        "--video",
        default=str(
            REPO_ROOT / "monitoring" / "videoplayback.mp4"
        ),
        help="Path to input video.",
    )
    parser.add_argument(
        "--yolo-pt",
        default=str(REPO_ROOT / "interface" / "backend" / "AI" / "yolov11n.pt"),
        help="Path to YOLO .pt model for CPU run.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "monitoring" / "testbench_outputs"),
        help="Base output directory for testbench artifacts.",
    )
    parser.add_argument(
        "--monitor-seconds",
        type=int,
        default=60,
        help="Monitoring duration in seconds.",
    )
    parser.add_argument(
        "--monitor-interval",
        type=int,
        default=5,
        help="Monitoring sample interval in seconds.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of runs per case (hailo and cpu).",
    )
    args = parser.parse_args()

    video_path = Path(args.video)
    yolo_pt = Path(args.yolo_pt) if args.yolo_pt else None
    output_base = Path(args.output_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    summary = {
        "started_at": datetime.datetime.now().isoformat(),
        "video": str(video_path),
        "monitor_seconds": args.monitor_seconds,
        "runs_per_case": args.runs,
        "hailo_available": is_hailo_hat_present(),
        "runs": {},
        "events": [],
    }

    stop_event = threading.Event()
    summary_path = output_base / "testbench_hat_session.json"
    summary_lock = threading.Lock()
    monitor_thread = threading.Thread(
        target=_monitoring_loop,
        args=(stop_event, args.monitor_interval, summary, summary_path, summary_lock),
        daemon=True,
    )

    if not video_path.exists():
        summary["ended_at"] = datetime.datetime.now().isoformat()
        summary["error"] = f"Video file not found: {video_path}"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Summary written to: {summary_path}")
        return

    start_energy_monitoring()
    monitor_thread.start()

    try:
        summary["runs"]["hailo"] = []
        summary["runs"]["cpu"] = []

        if summary["hailo_available"]:
            for i in range(1, args.runs + 1):
                summary["events"].append(
                    {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "event": "hailo_run_start",
                        "run_index": i,
                    }
                )
                summary["runs"]["hailo"].append(
                    _run_hailo(
                        video_path=video_path,
                        output_dir=output_base / "hailo",
                        run_index=i,
                    )
                )
                summary["events"].append(
                    {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "event": "hailo_run_end",
                        "run_index": i,
                    }
                )
        else:
            summary["runs"]["hailo"].append({"skipped": "Hailo not detected"})

        for i in range(1, args.runs + 1):
            summary["events"].append(
                {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "event": "cpu_run_start",
                    "run_index": i,
                }
            )
            summary["runs"]["cpu"].append(
                _run_cpu(
                    video_path=video_path,
                    output_dir=output_base / "cpu",
                    yolo_path=yolo_pt,
                    run_index=i,
                )
            )
            summary["events"].append(
                {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "event": "cpu_run_end",
                    "run_index": i,
                }
            )

        time.sleep(max(0, args.monitor_seconds))
    finally:
        stop_event.set()
        monitor_thread.join(timeout=5)
        stop_energy_monitoring()

    summary["ended_at"] = datetime.datetime.now().isoformat()

    def _read_json_if_exists(path: str) -> list | dict | None:
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None

    summary["monitoring_logs"] = {
        "energy": _read_json_if_exists(ENERGY_JSON_FILE),
        "temperature": _read_json_if_exists(TEMP_LOG_FILE),
        "camera": _read_json_if_exists(CAMERA_LOG_FILE),
        "hailo": _read_json_if_exists(HAILO_LOG_FILE),
        "memory": _read_json_if_exists("memory_log.json"),
        "disk": _read_json_if_exists("disk_log.json"),
        "current": _read_json_if_exists(glob_filename),
    }

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary written to: {summary_path}")


if __name__ == "__main__":
    main()
