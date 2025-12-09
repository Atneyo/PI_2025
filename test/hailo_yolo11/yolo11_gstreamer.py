from pathlib import Path
import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import hailo

from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad
from hailo_apps.hailo_app_python.core.common.core import get_default_parser
from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp


class UserCallback(app_callback_class):
    def __init__(self):
        super().__init__()


def app_callback(pad, info, user_data):
    buf = info.get_buffer()
    if buf is None:
        return Gst.PadProbeReturn.OK

    user_data.increment()
    frame_id = user_data.get_count()

    roi = hailo.get_roi_from_buffer(buf)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    print(f"\nFrame {frame_id} - {len(detections)} detections")

    for d in detections:
        print(f" - {d.get_label()} conf={d.get_confidence():.3f}")

    return Gst.PadProbeReturn.OK


def build_parser(default_video: Path, default_hef: Path):
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
    return parser


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    env_file = root / ".env"
    os.environ["HAILO_ENV_FILE"] = str(env_file)

    print("== Using ENV ==")
    print(env_file.read_text())

    default_video = root / "resources" / "videoplayback.mp4"
    default_hef = root / "yolov11n.hef"
    parser = build_parser(default_video, default_hef)

    user_data = UserCallback()
    app = GStreamerDetectionApp(app_callback, user_data, parser=parser)
    app.run()
