from pathlib import Path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import os
import hailo

from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad
from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp


# =========================================================================
#  Classe callback utilisateur (même principe que ton script qui marche)
# =========================================================================
class UserAppCallback(app_callback_class):
    def __init__(self):
        super().__init__()   # compteur de frames, etc.


# =========================================================================
#  Callback appelé à chaque frame après le réseau Hailo (YOLOv11)
# =========================================================================
def app_callback(pad, info, user_data):
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Compter les frames
    user_data.increment()
    frame_id = user_data.get_count()

    # (optionnel) lire les caps si besoin
    fmt, w, h = get_caps_from_pad(pad)

    # Récupérer les détections déjà post-traitées par Hailo
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    log = [f"\nFrame {frame_id} - {len(detections)} détection(s)"]
    for det in detections:
        label = det.get_label()
        conf = det.get_confidence()
        bbox = det.get_bbox()
        log.append(f"  - {label}  conf={conf:.2f}  bbox={bbox}")

    print("\n".join(log))

    # ⚠️ On ne fait PAS de cv2.imshow ici : callback ≠ thread principal
    # L’OSD (boxes) est géré par la pipeline GStreamer de Hailo.

    return Gst.PadProbeReturn.OK


# =========================================================================
#  MAIN
# =========================================================================
if __name__ == "__main__":
    # Pointage vers ton .env
    project_root = Path(__file__).resolve().parent
    env_file = project_root / ".env"
    os.environ["HAILO_ENV_FILE"] = str(env_file)

    # Instance de la classe de callback
    user_data = UserAppCallback()

    # Création de l’app GStreamer préconfigurée par Hailo
    app = GStreamerDetectionApp(
        app_callback,   # fonction callback
        user_data       # objet utilisateur (compteur, etc.)
    )

    # Lance la pipeline :
    #  - v4l2src /dev/video0
    #  - pré-process
    #  - YOLOv11n.hef sur Hailo8L
    #  - post-process + overlay
    #  - autovideosink (fenêtre vidéo avec boxes)
    app.run()
