from pathlib import Path
from datetime import datetime
import os
import shlex
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import hailo
import time

from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.core.common.core import get_default_parser
from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import (
    SOURCE_PIPELINE,
    INFERENCE_PIPELINE,
    INFERENCE_PIPELINE_WRAPPER,
    TRACKER_PIPELINE,
    USER_CALLBACK_PIPELINE,
    DISPLAY_PIPELINE,
    QUEUE,
)


class UserCallback(app_callback_class):
    def __init__(self, stats_interval: int = 60):
        super().__init__()
        self.stats_interval = max(1, stats_interval)
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

    print(f"\nFrame {frame_id} - {detection_count} detections")

    for d in detections:
        print(f" - {d.get_label()} conf={d.get_confidence():.3f}")

    user_data.record_detections(detection_count)
    user_data.maybe_print_stats()

    return Gst.PadProbeReturn.OK


def build_parser(default_video: Path, default_hef: Path, default_recording: Path):
    """Create parser with sensible defaults and convenient source selectors."""
    parser = get_default_parser()

    if default_video.exists():
        parser.set_defaults(input=str(default_video))
    if default_hef.exists():
        parser.set_defaults(hef_path=str(default_hef))

    parser.add_argument(
        "--video",
        dest="input",
        metavar="PATH",
        help=f"Path to a video file (default: {default_video})",
    )
    parser.add_argument(
        "--webcam",
        action="store_const",
        const="usb",
        dest="input",
        help="Use the first detected USB camera as input.",
    )
    parser.add_argument(
        "--pi-camera",
        action="store_const",
        const="rpi",
        dest="input",
        help="Use the Raspberry Pi CSI camera module as input.",
    )
    parser.add_argument(
        "--record-output",
        default=str(default_recording),
        help="Path to the recorded video (default: recordings directory with timestamp).",
    )
    parser.add_argument(
        "--record-bitrate",
        type=int,
        default=8000,
        help="Video bitrate (kbps) used when encoding the recorded file.",
    )
    parser.add_argument(
        "--audio-source",
        default="autoaudiosrc",
        help="Audio source element used for recording (e.g. autoaudiosrc, pulsesrc, alsasrc).",
    )
    parser.add_argument(
        "--audio-device",
        default=None,
        help="Optional device property passed to the audio source.",
    )
    parser.add_argument(
        "--audio-bitrate",
        type=int,
        default=128000,
        help="Audio bitrate in bits per second.",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Disable audio capture when recording the output.",
    )
    parser.add_argument(
        "--disable-recording",
        action="store_true",
        help="Run without saving the annotated video to disk.",
    )
    parser.add_argument(
        "--loop-file-source",
        action="store_true",
        help="Rebuild the pipeline after EOS when using a file source (default: stop after a single pass).",
    )
    parser.add_argument(
        "--stats-interval",
        type=int,
        default=60,
        help="Number of frames between FPS/statistics log lines.",
    )
    return parser


class RecordingDetectionApp(GStreamerDetectionApp):
    """Detection app that can duplicate the annotated stream to a file sink with audio."""

    def __init__(self, app_callback, user_data, parser=None, parsed_args=None):
        if parser is None:
            parser = get_default_parser()
        if parsed_args is None:
            parsed_args, _ = parser.parse_known_args()

        self.record_enabled = not getattr(parsed_args, "disable_recording", False)
        self.record_output = Path(parsed_args.record_output).expanduser()
        self.record_bitrate = getattr(parsed_args, "record_bitrate", 8000)
        self.audio_source = getattr(parsed_args, "audio_source", "autoaudiosrc")
        self.audio_device = getattr(parsed_args, "audio_device", None)
        self.audio_bitrate = getattr(parsed_args, "audio_bitrate", 128000)
        self.include_audio = not getattr(parsed_args, "no_audio", False)
        self.loop_file_source = bool(getattr(parsed_args, "loop_file_source", False))
        self.record_tee_name = "record_tee"
        self.record_mux_name = "record_mux"

        if self.record_enabled:
            self.record_output.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(app_callback, user_data, parser=parser)

    def _quote_path(self, path: Path) -> str:
        return shlex.quote(str(path))

    def _audio_source_string(self) -> str:
        params = []
        if self.audio_device:
            params.append(f"device={self.audio_device}")
        param_str = f" {' '.join(params)}" if params else ""
        return f"{self.audio_source} name=record_audio_src{param_str}"

    def _record_video_branch(self) -> str:
        return (
            f"{QUEUE(name='record_branch_q', max_size_buffers=10)} ! "
            f"videoconvert name=record_videoconvert n-threads=2 qos=false ! "
            f"{QUEUE(name='record_enc_q', max_size_buffers=10)} ! "
            f"x264enc tune=zerolatency bitrate={self.record_bitrate} key-int-max=30 "
            f"speed-preset=ultrafast bframes=0 ! "
            f"{QUEUE(name='record_mux_video_q', max_size_buffers=10)} ! "
            f"{self.record_mux_name}. "
        )

    def _audio_branch(self) -> str:
        if not self.include_audio:
            return ""
        return (
            f"{self._audio_source_string()} ! "
            f"{QUEUE(name='record_audio_q', max_size_buffers=20)} ! "
            f"audioconvert name=record_audio_convert ! "
            f"audioresample name=record_audio_resample ! "
            f"voaacenc bitrate={self.audio_bitrate} ! "
            f"{QUEUE(name='record_audio_mux_q', max_size_buffers=10)} ! "
            f"{self.record_mux_name}. "
        )

    def _mux_block(self) -> str:
        return (
            f"matroskamux name={self.record_mux_name} writing-app=HailoDetectionApp streamable=true ! "
            f"filesink location={self._quote_path(self.record_output)} async=false "
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
        display_pipeline = DISPLAY_PIPELINE(
            video_sink=self.video_sink, sync=self.sync, show_fps=self.show_fps
        )

        display_branch = f"{QUEUE(name='display_branch_q')} ! {display_pipeline}"
        record_branch = self._record_video_branch()
        audio_branch = self._audio_branch()
        mux_block = self._mux_block()

        pipeline_string = (
            f"{source_pipeline} ! "
            f"{detection_wrapper} ! "
            f"{tracker_pipeline} ! "
            f"{user_callback_pipeline} ! "
            f"tee name={self.record_tee_name} "
            f"{self.record_tee_name}. ! {display_branch} "
            f"{self.record_tee_name}. ! {record_branch}"
            f"{audio_branch}"
            f"{mux_block}"
        )
        return pipeline_string

    def on_eos(self):
        """Stop instead of looping when using file sources unless explicitly requested."""
        if self.source_type == "file" and not self.loop_file_source:
            print("End-of-stream reached. Stopping recording...")
            self.shutdown()
        else:
            super().on_eos()


def _prepare_parser(record_output_dir: Path | None = None):
    """Initialize the environment, ensure the recording directory exists, and build the parser."""
    root = Path(__file__).resolve().parent
    env_file = root / ".env"
    os.environ["HAILO_ENV_FILE"] = str(env_file)

    print("== Using ENV ==")
    print(env_file.read_text())

    default_video = root / "resources" / "videoplayback.mp4"
    default_hef = root / "yolov11n.hef"

    if record_output_dir is None:
        record_output_dir = root / "recordings"
    record_output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_recording = Path(record_output_dir) / f"detections_{timestamp}.mkv"
    parser = build_parser(default_video, default_hef, default_recording)
    return parser, default_recording


def _run_with_args(parser, parsed_args):
    """Create the app, attach callbacks, and run the pipeline."""
    user_data = UserCallback(stats_interval=parsed_args.stats_interval)
    app = RecordingDetectionApp(app_callback, user_data, parser=parser, parsed_args=parsed_args)
    if app.record_enabled:
        print(f"Recording detection stream to: {app.record_output}")
        user_data.set_recording_target(app.record_output)

    try:
        app.run()
    finally:
        user_data.print_summary()


def run_detection_session(
    live_input: bool,
    video_path: str | Path | None,
    output_dir: str | Path | None,
    extra_cli_args: list[str] | None = None,
):
    """Programmatic helper to launch detection either from webcam (live) or a video file.

    Args:
        live_input (bool): When True, uses the first detected USB webcam as the source.
        video_path (str | Path | None): Path to a video file when live_input is False.
        output_dir (str | Path | None): Directory where the recorded output file will be stored.
        extra_cli_args (list[str] | None): Optional CLI-style overrides appended when spawning the pipeline.

    Returns:
        Path: The recording path used for the current session.
    """
    root = Path(__file__).resolve().parent
    output_dir = Path(output_dir) if output_dir is not None else (root / "recordings")
    parser, default_recording = _prepare_parser(record_output_dir=output_dir)

    cli_args = []
    if live_input:
        cli_args.append("--webcam")
    else:
        if video_path is None:
            raise ValueError("video_path must be provided when live_input is False.")
        cli_args.extend(["--video", str(video_path)])

    cli_args.extend(["--record-output", str(default_recording)])
    if extra_cli_args:
        cli_args.extend(extra_cli_args)
    parsed_args = parser.parse_args(cli_args)

    old_argv = sys.argv[:]
    try:
        sys.argv = [old_argv[0]] + cli_args
        _run_with_args(parser, parsed_args)
    finally:
        sys.argv = old_argv

    return default_recording


def yolo_detection(
    live_input: bool = True,
    video_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    extra_cli_args: list[str] | None = None,
) -> Path:
    """High-level helper tailored for FastAPI routes.

    Example usage inside a route:
        @router.post(\"/detect\")
        def detect(payload: DetectionRequest):
            recorded_path = yolo_detection(
                live_input=payload.use_webcam,
                video_path=payload.video_path,
                output_dir=\"/tmp/recordings\",
            )
            return {\"recording\": str(recorded_path)}

    Args mirror run_detection_session. The return value is the saved MKV path.
    """
    return run_detection_session(live_input, video_path, output_dir, extra_cli_args)


if __name__ == "__main__":
    parser, _ = _prepare_parser()
    parsed_args, _ = parser.parse_known_args()
    _run_with_args(parser, parsed_args)
