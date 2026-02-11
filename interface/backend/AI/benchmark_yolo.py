from pathlib import Path
import json
import statistics
import time
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from interface.backend.AI.yolo_detection import yolo_detection

NB_RUNS = 20


def load_stats(json_path: Path) -> dict:
    if not json_path.exists():
        raise FileNotFoundError(f"Stats file not found: {json_path}")
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    all_stats = []

    print(f"🚀 Starting benchmark ({NB_RUNS} runs)\n")

    for i in range(1, NB_RUNS + 1):
        print(f"▶ Run {i}/{NB_RUNS}")
        video_path = "interface/backend/AI/videoplayback.mp4"
        output_video = yolo_detection(
                        live_input=False,
                        video_path=video_path,
                        frame_rate=5,
                        output_dir="interface/backend/outputs",
                        record_filename="video.mp4",
                    )

        stats_path = output_video.with_suffix(".json")

        stats = load_stats(stats_path)
        all_stats.append(stats)

        print(f"  Frames: {stats['frames_processed']}, "
              f"Avg FPS: {stats['average_fps']}, "
              f"Detections: {stats['total_detections']}")

        time.sleep(1)  # petite pause pour éviter de saturer le système

    # === Agrégation des résultats ===
    aggregated = {
        "frames_processed": [],
        "total_time_seconds": [],
        "average_fps": [],
        "total_detections": [],
        "peak_detections_per_frame": [],
    }

    for stats in all_stats:
        for key in aggregated:
            aggregated[key].append(stats[key])

    averages = {
        key: round(statistics.mean(values), 3)
        for key, values in aggregated.items()
    }

    # === Résultat final ===
    print("\n📊 ===== BENCHMARK SUMMARY =====")
    print(f"Runs: {NB_RUNS}")
    print(f"Average frames processed: {averages['frames_processed']}")
    print(f"Average total time (s): {averages['total_time_seconds']}")
    print(f"Average FPS: {averages['average_fps']}")
    print(f"Average total detections: {averages['total_detections']}")
    print(f"Average peak detections/frame: {averages['peak_detections_per_frame']}")

    # Sauvegarde optionnelle
    output_file = Path("benchmark_summary.json")
    output_file.write_text(
        json.dumps(
            {
                "runs": NB_RUNS,
                "averages": averages,
                "raw_results": all_stats,
            },
            indent=2
        ),
        encoding="utf-8",
    )

    print(f"\n💾 Benchmark saved to: {output_file.resolve()}")


if __name__ == "__main__":
    main()
