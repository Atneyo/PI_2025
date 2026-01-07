from pathlib import Path
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import hailo

from interface.backend.AI.cropping_yolo import (
    extract_frame_from_pad,
    save_detection_crops,
)
from interface.backend.AI.download_yolo import (
    crop_output_dir,
    recording_output_path,
)
from interface.backend.AI.gstreamer_yolo import (
    RecordingDetectionApp,
    runtime_namespace,
)
from interface.backend.AI.stats_yolo import UserCallback, write_summary_json

MODULE_ROOT = Path(__file__).resolve().parent
ENV_FILE_PATH = MODULE_ROOT / ".env"
HEF_FILE = MODULE_ROOT / "yolov11n.hef"
RECORDINGS_DIR = MODULE_ROOT / "recordings"
DEFAULT_VIDEO = MODULE_ROOT / "resources" / "videoplayback.mp4"

# === Simple knobs to tweak ===
USE_WEBCAM = True  # False to run on DEFAULT_VIDEO
RECORD_FILENAME = "detections_latest.mkv"
FRAME_RATE = 15
ARCH = None  # e.g. "hailo8"
SHOW_FPS = False
USE_FRAME_QUEUE = False
SYNC_WITH_SOURCE = True
ENABLE_CALLBACK = True
DUMP_PIPELINE_GRAPH = False
UI_MODE = False
LABELS_JSON = None

ENABLE_RECORDING = True
RECORD_BITRATE = 8000
LOOP_FILE_SOURCE = False

STATS_INTERVAL = 60
LOG_INTERVAL = 300
TRACK_STALE_FRAMES = 30


def app_callback(pad, info, user_data):
    buf = info.get_buffer()
    if buf is None:
        return Gst.PadProbeReturn.OK

    user_data.increment()
    frame_id = user_data.get_count()

    frame = None
    width = None
    height = None
    if user_data.crop_dir is not None:
        frame, width, height = extract_frame_from_pad(pad, buf)

    roi = hailo.get_roi_from_buffer(buf)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    detection_count = len(detections)

    if user_data.should_log_frame(frame_id):
        summary = ", ".join(d.get_label() for d in detections[:3]) if detections else "none"
        print(f"[Frame {frame_id}] detections={detection_count} sample={summary}")

    if (
        frame is not None
        and user_data.crop_dir is not None
        and width is not None
        and height is not None
    ):
        save_detection_crops(
            frame,
            width,
            height,
            detections,
            user_data.crop_dir,
            frame_id,
            id_resolver=user_data.get_global_id,
        )

    user_data.record_detections(detection_count)
    user_data.maybe_print_stats()

    return Gst.PadProbeReturn.OK


def load_detection_environment(env_file: str | Path | None = None) -> Path:
    """Set the env file that Hailo expects and print its contents for visibility."""
    env_path = Path(env_file) if env_file is not None else ENV_FILE_PATH
    os.environ["HAILO_ENV_FILE"] = str(env_path)
    print("== Using ENV ==")
    print(env_path.read_text())
    return env_path


def yolo_detection(
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
    use_frame: bool = USE_FRAME_QUEUE,
    sync_with_source: bool = SYNC_WITH_SOURCE,
    enable_callback: bool = ENABLE_CALLBACK,
    dump_pipeline_graph: bool = DUMP_PIPELINE_GRAPH,
    env_file: str | Path | None = None,
    arch: str | None = None,
    hef_path: str | Path | None = None,
) -> Path:
    """Launch the YOLO detection pipeline with the requested source."""
    if not live_input and video_path is None:
        raise ValueError("video_path must be provided when live_input is False.")

    frame_rate = frame_rate or FRAME_RATE
    record_bitrate = record_bitrate or RECORD_BITRATE
    stats_interval = stats_interval or STATS_INTERVAL
    log_interval = log_interval or LOG_INTERVAL
    arch = arch or ARCH

    runtime_ns = runtime_namespace(
        live_input=live_input,
        video_path=video_path,
        frame_rate=frame_rate,
        arch=arch,
        hef_override=hef_path,
        show_fps=show_fps,
        use_frame=use_frame,
        sync_with_source=sync_with_source,
        enable_callback=enable_callback,
        dump_pipeline_graph=dump_pipeline_graph,
        ui_mode=UI_MODE,
        labels_json=LABELS_JSON,
        hef_default=HEF_FILE,
    )
    record_output = recording_output_path(record_filename, output_dir, RECORDINGS_DIR)
    crop_dir = crop_output_dir(output_dir, RECORDINGS_DIR)

    load_detection_environment(env_file)
    user_data = UserCallback(
        stats_interval=stats_interval,
        log_interval=log_interval,
        track_stale_frames=TRACK_STALE_FRAMES,
    )
    app = RecordingDetectionApp(
        app_callback,
        user_data,
        runtime_namespace=runtime_ns,
        record_output=record_output,
        enable_recording=enable_recording,
        record_bitrate=record_bitrate,
        loop_file_source=loop_file_source,
    )

    if app.record_enabled:
        print(f"Recording detection stream to: {app.record_output}")
        user_data.set_recording_target(app.record_output)
    user_data.set_crop_dir(crop_dir)

    finalized_recording: Path | None = None
    try:
        app.run()
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 0
        if exit_code not in (0, 1, None):
            raise RuntimeError(f"GStreamerDetectionApp exited with code {exit_code}") from None
    finally:
        try:
            finalized_recording = app.finalize_recording()
            target_path = finalized_recording or app.record_output
            write_summary_json(user_data, target_path)
        finally:
            user_data.print_summary()

    return finalized_recording or app.record_output


if __name__ == "__main__":
    yolo_detection()
