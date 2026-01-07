from __future__ import annotations

from pathlib import Path
from typing import Dict
import json
import time

from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class


class UserCallback(app_callback_class):
    def __init__(
        self,
        stats_interval: int = 60,
        log_interval: int = 300,
        track_stale_frames: int = 30,
    ):
        super().__init__()
        self.stats_interval = max(1, stats_interval)
        self.log_interval = max(1, log_interval)
        self.track_stale_frames = max(1, track_stale_frames)
        self.start_time = time.perf_counter()
        self.last_stats_time = self.start_time
        self.last_stats_frame = 0
        self.total_detections = 0
        self.max_detections = 0
        self.recording_target = None
        self.crop_dir = None
        self._next_global_id = 1
        self._track_last_seen: Dict[int, int] = {}
        self._track_global_id: Dict[int, int] = {}

    def record_detections(self, detection_count: int):
        self.total_detections += detection_count
        if detection_count > self.max_detections:
            self.max_detections = detection_count

    def maybe_print_stats(self):
        frame_id = self.frame_count
        frames_since = frame_id - self.last_stats_frame
        if frames_since < self.stats_interval:
            return

        now = time.perf_counter()
        window_seconds = now - self.last_stats_time
        window_fps = frames_since / window_seconds if window_seconds > 0 else 0.0
        total_seconds = now - self.start_time
        avg_fps = frame_id / total_seconds if total_seconds > 0 else 0.0

        print(
            f"[Stats] Frames={frame_id} AvgFPS={avg_fps:.2f} "
            f"WindowFPS={window_fps:.2f} TotalDetections={self.total_detections} "
            f"PeakPerFrame={self.max_detections}"
        )

        self.last_stats_frame = frame_id
        self.last_stats_time = now

    def should_log_frame(self, frame_id: int) -> bool:
        return frame_id == 1 or (frame_id % self.log_interval == 0)

    def set_recording_target(self, target: Path):
        self.recording_target = target

    def set_crop_dir(self, target: Path):
        self.crop_dir = target

    def print_summary(self):
        total_seconds = time.perf_counter() - self.start_time
        avg_fps = self.frame_count / total_seconds if total_seconds > 0 else 0.0

        print("\n== Session summary ==")
        print(f"Frames processed: {self.frame_count}")
        print(f"Total time: {total_seconds:.2f}s")
        print(f"Average FPS: {avg_fps:.2f}")
        print(f"Total detections: {self.total_detections}")
        print(f"Peak detections/frame: {self.max_detections}")
        if self.recording_target:
            print(f"Recorded video: {self.recording_target}")

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

    def get_global_id(self, track_id: int, frame_id: int) -> int:
        last_seen = self._track_last_seen.get(track_id)
        if last_seen is None or (frame_id - last_seen) > self.track_stale_frames:
            global_id = self._next_global_id
            self._next_global_id += 1
            self._track_global_id[track_id] = global_id
        else:
            global_id = self._track_global_id[track_id]

        self._track_last_seen[track_id] = frame_id
        return global_id


def write_summary_json(user_data: UserCallback, target_path: Path) -> Path:
    summary_path = target_path.with_suffix(".json")
    summary_payload = user_data.to_summary_dict()
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
    return summary_path
