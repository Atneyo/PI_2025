"""Quick helper script to validate yolo_detection from FastAPI-friendly module."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_detection_module():
    """Import `yolo11_gstreamer copy.py` even though file name contains spaces."""
    module_path = Path(__file__).resolve().parent / "yolo11_gstreamer copy.py"
    spec = importlib.util.spec_from_file_location("yolo11_gstreamer_copy", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load detection script from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    project_root = Path(__file__).resolve().parent
    resources_video = project_root / "resources" / "videoplayback.mp4"

    if not resources_video.exists():
        raise FileNotFoundError(f"Sample video not found: {resources_video}")

    output_dir = project_root / "recordings_tests"
    output_dir.mkdir(parents=True, exist_ok=True)
    recording_target = output_dir / "test_detection_recording.mkv"

    detector = _load_detection_module()
    print(f"Running detection on {resources_video} -> {recording_target}")

    detector.yolo_detection(
        live_input=False,
        video_path=resources_video,
        output_dir=output_dir,
        extra_cli_args=["--record-output", str(recording_target)],
    )

    print(f"Recording complete: {recording_target}")


if __name__ == "__main__":
    main()
