from __future__ import annotations

from pathlib import Path
import shlex
from types import SimpleNamespace

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

from interface.backend.AI.download_yolo import temporary_recording_path


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


def runtime_namespace(
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
    ui_mode: bool,
    labels_json: str | Path | None,
    hef_default: Path,
) -> SimpleNamespace:
    """Return the minimal namespace GStreamerApp expects."""
    input_source = "usb" if live_input else str(video_path)
    hef_path = None
    if hef_override:
        hef_path = str(hef_override)
    elif hef_default.exists():
        hef_path = str(hef_default)

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
        ui=ui_mode,
        labels_json=labels_json,
    )


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
        self.record_tmp_output = temporary_recording_path(self.record_output)
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

        ########################### here are the lines that will make the detection with the hailo library #########################################

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
        tracker_pipeline = TRACKER_PIPELINE(
            class_id=-1,
            keep_tracked_frames=1,
            keep_lost_frames=0,
            keep_new_frames=0,
        )
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
