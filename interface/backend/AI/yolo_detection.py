from pathlib import Path
from datetime import datetime
import os
import shlex
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import hailo
import time
from types import SimpleNamespace

from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import (
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    OVERLAY_PIPELINE,
    QUEUE,
)

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


class FixedArgsParser:
    """Minimal parser-like object returning a pre-built namespace to Hailo's app."""

    def __init__(self, namespace: SimpleNamespace):
        self._namespace = namespace

    def add_argument(self, *names, **kwargs):
        dest = kwargs.get("dest")
        if not dest:
            for name in reversed(names):
                if name.startswith("--"):
                    dest = name.lstrip("-").replace("-", "_")
                    break
        if dest and not hasattr(self._namespace, dest):
            setattr(self._namespace, dest, kwargs.get("default"))

    def parse_args(self):
        return SimpleNamespace(**vars(self._namespace))


def _runtime_namespace(
    *,
    live_input: bool,
    video_path: str | Path | None,
    frame_rate: int,
    arch: str | None,
    hef_override: str | Path | None,
    show_fps: bool,
    use_frame: bool,
    sync_with_source: bool,
    enable_callback: bool,
    dump_pipeline_graph: bool,
) -> SimpleNamespace:
    """Return the minimal namespace GStreamerApp expects."""
    input_source = "usb" if live_input else str(video_path)
    hef_path = None
    if hef_override:
        hef_path = str(hef_override)
    elif HEF_FILE.exists():
        hef_path = str(HEF_FILE)

    return SimpleNamespace(
        input=input_source,
        frame_rate=frame_rate,
        arch=arch,
        hef_path=hef_path,
        use_frame=use_frame,
        show_fps=show_fps,
        disable_sync=not sync_with_source,
        disable_callback=not enable_callback,
        dump_dot=dump_pipeline_graph,
        ui=UI_MODE,
        labels_json=LABELS_JSON,
    )


def _recording_output_path(record_filename: str | None, output_dir: str | Path | None) -> Path:
    """Ensure the recordings directory exists and return the selected file path."""
    base_dir = Path(output_dir) if output_dir is not None else RECORDINGS_DIR
    base_dir.mkdir(parents=True, exist_ok=True)
    if record_filename:
        candidate = Path(record_filename)
        if candidate.is_absolute():
            return candidate
        return (base_dir / candidate).resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (base_dir / f"detections_{timestamp}.mkv").resolve()


def _temporary_recording_path(target_path: Path) -> Path:
    """Return the `.part` file used while the pipeline is still running."""
    return target_path.with_name(f"{target_path.name}.part")


class UserCallback(app_callback_class):
    def __init__(self, stats_interval: int = 60, log_interval: int = 300):
        super().__init__()
        self.stats_interval = max(1, stats_interval)
        self.log_interval = max(1, log_interval)
        self.start_time = time.perf_counter()
        self.last_stats_time = self.start_time
        self.last_stats_frame = 0
        self.total_detections = 0
        self.max_detections = 0
        self.recording_target = None

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


def app_callback(pad, info, user_data):
    buf = info.get_buffer()
    if buf is None:
        return Gst.PadProbeReturn.OK

    user_data.increment()
    frame_id = user_data.get_count()

    roi = hailo.get_roi_from_buffer(buf)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    detection_count = len(detections)

    if user_data.should_log_frame(frame_id):
        summary = ", ".join(d.get_label() for d in detections[:3]) if detections else "none"
        print(f"[Frame {frame_id}] detections={detection_count} sample={summary}")

    user_data.record_detections(detection_count)
    user_data.maybe_print_stats()

    return Gst.PadProbeReturn.OK


class RecordingDetectionApp(GStreamerDetectionApp):
    """Detection app that can duplicate the annotated stream to a file sink."""

    def __init__(
        self,
        app_callback,
        user_data,
        *,
        runtime_namespace: SimpleNamespace,
        record_output: Path,
        enable_recording: bool,
        record_bitrate: int,
        loop_file_source: bool,
    ):
        parser = FixedArgsParser(runtime_namespace)

        self.record_enabled = enable_recording
        self.record_output = record_output
        self.record_tmp_output = _temporary_recording_path(self.record_output)
        try:
            self.record_tmp_output.unlink(missing_ok=True)
        except TypeError:
            # Python < 3.8 compatibility
            if self.record_tmp_output.exists():
                self.record_tmp_output.unlink()
        self.record_bitrate = record_bitrate
        self.loop_file_source = loop_file_source
        self.record_mux_name = "record_mux"

        super().__init__(app_callback, user_data, parser=parser)

    def _quote_path(self, path: Path) -> str:
        return shlex.quote(str(path))

    def _record_video_branch(self) -> str:
        overlay = OVERLAY_PIPELINE(name="record_overlay")
        target_caps = (
            f"video/x-raw, width={self.video_width}, height={self.video_height}, pixel-aspect-ratio=1/1"
        )
        mux = (
            f"matroskamux name={self.record_mux_name} "
            "writing-app=HailoDetectionApp streamable=true ! "
        )
        return (
            f"{QUEUE(name='record_branch_q', max_size_buffers=10)} ! "
            f"{overlay}! "
            f"{QUEUE(name='record_scale_q', max_size_buffers=10)} ! "
            f"videoscale name=record_videoscale n-threads=2 ! "
            f"{QUEUE(name='record_caps_q', max_size_buffers=10)} ! "
            f'capsfilter name=record_caps caps="{target_caps}" ! '
            f"{QUEUE(name='record_videoconvert_q', max_size_buffers=10)} ! "
            f"videoconvert name=record_videoconvert n-threads=2 qos=false ! "
            f"{QUEUE(name='record_enc_q', max_size_buffers=10)} ! "
            f"x264enc tune=zerolatency bitrate={self.record_bitrate} key-int-max=30 "
            f"speed-preset=ultrafast bframes=0 ! "
            f"{QUEUE(name='record_mux_video_q', max_size_buffers=10)} ! "
            f"{mux}"
            f"{QUEUE(name='record_filesink_q', max_size_buffers=5)} ! "
            f"filesink location={self._quote_path(self.record_tmp_output)} async=false "
        )

    def get_pipeline_string(self):
        if not self.record_enabled:
            return super().get_pipeline_string()

        source_pipeline = SOURCE_PIPELINE(
            video_source=self.video_source,
            video_width=self.video_width,
            video_height=self.video_height,
            frame_rate=self.frame_rate,
            sync=self.sync,
        )
        detection_pipeline = INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            post_function_name=self.post_function_name,
            batch_size=self.batch_size,
            config_json=self.labels_json,
            additional_params=self.thresholds_str,
        )
        detection_wrapper = INFERENCE_PIPELINE_WRAPPER(detection_pipeline)
        tracker_pipeline = TRACKER_PIPELINE(class_id=1)
        user_callback_pipeline = USER_CALLBACK_PIPELINE()
        record_branch = self._record_video_branch()

        pipeline_string = (
            f"{source_pipeline} ! "
            f"{detection_wrapper} ! "
            f"{tracker_pipeline} ! "
            f"{user_callback_pipeline} ! "
            f"{record_branch}"
        )
        return pipeline_string

    def on_eos(self):
        """Stop instead of looping when using file sources unless explicitly requested."""
        if self.source_type == "file" and not self.loop_file_source:
            print("End-of-stream reached. Stopping recording...")
            self.shutdown()
        else:
            super().on_eos()

    def finalize_recording(self) -> Path | None:
        """Rename the temporary recording file once GStreamer flushed all data."""
        if not self.record_enabled:
            return None

        tmp_path = self.record_tmp_output
        final_path = self.record_output

        if not tmp_path.exists():
            print(f"No recording produced (missing file: {tmp_path})")
            return None

        size = tmp_path.stat().st_size
        if size == 0:
            try:
                tmp_path.unlink(missing_ok=True)
            except TypeError:
                if tmp_path.exists():
                    tmp_path.unlink()
            raise RuntimeError("Recording pipeline produced an empty file.")

        final_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.replace(final_path)
        return final_path


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

    runtime_namespace = _runtime_namespace(
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
    )
    record_output = _recording_output_path(record_filename, output_dir)

    load_detection_environment(env_file)
    user_data = UserCallback(stats_interval=stats_interval, log_interval=log_interval)
    app = RecordingDetectionApp(
        app_callback,
        user_data,
        runtime_namespace=runtime_namespace,
        record_output=record_output,
        enable_recording=enable_recording,
        record_bitrate=record_bitrate,
        loop_file_source=loop_file_source,
    )

    if app.record_enabled:
        print(f"Recording detection stream to: {app.record_output}")
        user_data.set_recording_target(app.record_output)

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
        finally:
            user_data.print_summary()

    return finalized_recording or app.record_output


if __name__ == "__main__":
    yolo_detection()
