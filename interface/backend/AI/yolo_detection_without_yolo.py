from __future__ import annotations

from pathlib import Path
import json
import time

import cv2

try:
    from ultralytics import YOLO
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "ultralytics is required for yolo_detection_without_yolo. "
        "Install it with: pip install ultralytics"
    ) from exc

def recording_output_path(record_filename: str | None, output_dir: str | Path | None, recordings_dir: Path) -> Path:
    """
    Build a writable path for the final recording.
    Ensures the destination directory exists and falls back to the default recordings directory.
    """
    base_dir = Path(output_dir) if output_dir else recordings_dir
    base_dir.mkdir(parents=True, exist_ok=True)
    filename = record_filename or RECORD_FILENAME
    filename_path = Path(filename)
    if not filename_path.suffix:
        filename_path = filename_path.with_suffix(".mp4")
    return base_dir / filename_path.name


def temporary_recording_path(record_output: Path) -> Path:
    """Create a temporary sibling path to avoid leaving a partial output file on failure."""
    return record_output.with_name(f"{record_output.stem}.tmp{record_output.suffix}")

MODULE_ROOT = Path(__file__).resolve().parent
YOLO_FILE = MODULE_ROOT / "yolov11n.pt"
RECORDINGS_DIR = MODULE_ROOT / "recordings"
DEFAULT_VIDEO = MODULE_ROOT / "resources" / "videoplayback.mp4"

# === Simple knobs to tweak ===
USE_WEBCAM = True
RECORD_FILENAME = "detections_latest.mkv"
FRAME_RATE = 15
SHOW_FPS = False
ENABLE_RECORDING = True
LOOP_FILE_SOURCE = False

STATS_INTERVAL = 60
LOG_INTERVAL = 300


class SimpleStats:
    def __init__(self, stats_interval: int, log_interval: int):
        self.stats_interval = max(1, stats_interval)
        self.log_interval = max(1, log_interval)
        self.start_time = time.perf_counter()
        self.last_stats_time = self.start_time
        self.last_stats_frame = 0
        self.frame_count = 0
        self.total_detections = 0
        self.max_detections = 0

    def update(self, detection_count: int):
        self.frame_count += 1
        self.total_detections += detection_count
        if detection_count > self.max_detections:
            self.max_detections = detection_count

    def should_log_frame(self) -> bool:
        return self.frame_count == 1 or (self.frame_count % self.log_interval == 0)

    def maybe_print_stats(self):
        frames_since = self.frame_count - self.last_stats_frame
        if frames_since < self.stats_interval:
            return

        now = time.perf_counter()
        window_seconds = now - self.last_stats_time
        window_fps = frames_since / window_seconds if window_seconds > 0 else 0.0
        total_seconds = now - self.start_time
        avg_fps = self.frame_count / total_seconds if total_seconds > 0 else 0.0

        print(
            f"[Stats] Frames={self.frame_count} AvgFPS={avg_fps:.2f} "
            f"WindowFPS={window_fps:.2f} TotalDetections={self.total_detections} "
            f"PeakPerFrame={self.max_detections}"
        )

        self.last_stats_frame = self.frame_count
        self.last_stats_time = now

    def average_fps(self) -> float:
        total_seconds = time.perf_counter() - self.start_time
        return self.frame_count / total_seconds if total_seconds > 0 else 0.0

    def to_summary_dict(self) -> dict:
        total_seconds = time.perf_counter() - self.start_time
        avg_fps = self.frame_count / total_seconds if total_seconds > 0 else 0.0
        return {
            "frames_processed": self.frame_count,
            "total_time_seconds": round(total_seconds, 3),
            "average_fps": round(avg_fps, 2),
            "total_detections": self.total_detections,
            "peak_detections_per_frame": self.max_detections,
        }


def _open_capture(source) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video source: {source}")
    return cap


def _fourcc_candidates(suffix: str) -> list[str]:
    suffix = suffix.lower()
    if suffix == ".webm":
        return ["VP80", "VP90", "H264", "mp4v"]
    if suffix in {".mkv", ".avi"}:
        return ["H264", "XVID", "mp4v"]
    return ["mp4v", "avc1", "H264"]


def _open_writer(path: Path, fps: float, width: int, height: int) -> cv2.VideoWriter:
    for fourcc in _fourcc_candidates(path.suffix):
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*fourcc),
            fps,
            (width, height),
        )
        if writer.isOpened():
            return writer
    raise RuntimeError(f"Unable to open VideoWriter for: {path}")


def _overlay_fps(frame, fps: float):
    cv2.putText(
        frame,
        f"FPS: {fps:.2f}",
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )


def _write_summary_json(stats: SimpleStats, target_path: Path) -> Path:
    summary_path = target_path.with_suffix(".json")
    summary_path.write_text(json.dumps(stats.to_summary_dict(), indent=2), encoding="utf-8")
    return summary_path


def yolo_detection_without_yolo(
    live_input: bool = True,
    *,
    video_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    record_filename: str | None = None, 
    frame_rate: int | None = None,
    record_bitrate: int | None = None,
    enable_recording: bool = ENABLE_RECORDING,
    loop_file_source: bool = LOOP_FILE_SOURCE,
    stats_interval: int | None = None,
    log_interval: int | None = None,
    show_fps: bool = SHOW_FPS,
    use_frame: bool = False,
    sync_with_source: bool = True,
    enable_callback: bool = True,
    dump_pipeline_graph: bool = False,
    env_file: str | Path | None = None,
    arch: str | None = None,
    yolo_path: str | Path | None = None,
) -> Path:
    """Run YOLO (.pt) inference without Hailo and record an annotated video."""
    _ = (record_bitrate, use_frame, sync_with_source, dump_pipeline_graph, env_file, arch)

    if not live_input and video_path is None:
        raise ValueError("video_path must be provided when live_input is False.")

    if live_input:
        source = 0
    else:
        source = str(video_path or DEFAULT_VIDEO)

    model_path = Path(yolo_path) if yolo_path is not None else YOLO_FILE
    if not model_path.exists():
        raise FileNotFoundError(f"YOLO model not found: {model_path}")

    frame_rate = frame_rate or FRAME_RATE
    stats_interval = stats_interval or STATS_INTERVAL
    log_interval = log_interval or LOG_INTERVAL

    cap = _open_capture(source)
    try:
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to read from video source.")

        height, width = frame.shape[:2]
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        if input_fps is None or input_fps <= 0:
            input_fps = frame_rate
        target_fps = float(frame_rate or input_fps)

        record_output = recording_output_path(
            record_filename,
            output_dir,
            RECORDINGS_DIR,
        )
        temp_output = temporary_recording_path(record_output)

        writer = None
        if enable_recording:
            try:
                writer = _open_writer(temp_output, target_fps, width, height)
            except RuntimeError:
                if record_output.suffix.lower() == ".webm":
                    fallback_output = record_output.with_suffix(".mp4")
                    temp_output = temporary_recording_path(fallback_output)
                    writer = _open_writer(temp_output, target_fps, width, height)
                    record_output = fallback_output
                else:
                    raise

        model = YOLO(str(model_path))
        stats = SimpleStats(stats_interval=stats_interval, log_interval=log_interval)

        frame_index = 0
        skip = 1
        if input_fps > 0 and frame_rate:
            skip = max(1, round(input_fps / frame_rate))

        while True:
            frame_index += 1

            if skip > 1 and (frame_index % skip != 0):
                ret, frame = cap.read()
                if not ret:
                    if loop_file_source and not live_input:
                        cap.release()
                        cap = _open_capture(source)
                        ret, frame = cap.read()
                        if not ret:
                            break
                    else:
                        break
                continue

            results = model.predict(frame, verbose=False)
            result = results[0]
            boxes = result.boxes
            detection_count = len(boxes) if boxes is not None else 0
            stats.update(detection_count)

            if enable_callback:
                if stats.should_log_frame():
                    if boxes is not None and len(boxes):
                        class_ids = boxes.cls[:3].tolist()
                        sample = ", ".join(result.names[int(cls_id)] for cls_id in class_ids)
                    else:
                        sample = "none"
                    print(f"[Frame {stats.frame_count}] detections={detection_count} sample={sample}")
                stats.maybe_print_stats()

            annotated = result.plot()
            if show_fps:
                _overlay_fps(annotated, stats.average_fps())

            if writer is not None:
                writer.write(annotated)

            ret, frame = cap.read()
            if not ret:
                if loop_file_source and not live_input:
                    cap.release()
                    cap = _open_capture(source)
                    ret, frame = cap.read()
                    if not ret:
                        break
                else:
                    break

        if writer is not None:
            writer.release()
            temp_output.replace(record_output)

        _write_summary_json(stats, record_output)
        stats_summary = stats.to_summary_dict()
        print("\n== Session summary ==")
        print(f"Frames processed: {stats_summary['frames_processed']}")
        print(f"Average FPS: {stats_summary['average_fps']}")
        print(f"Total detections: {stats_summary['total_detections']}")
        print(f"Peak detections/frame: {stats_summary['peak_detections_per_frame']}")
        if enable_recording:
            print(f"Recorded video: {record_output}")

        return record_output
    finally:
        cap.release()


if __name__ == "__main__":
    yolo_detection_without_yolo()
