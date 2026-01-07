from __future__ import annotations

from pathlib import Path
import re

import cv2
import hailo
from hailo_apps.hailo_app_python.core.common.buffer_utils import (
    get_caps_from_pad,
    get_numpy_from_buffer,
)


def safe_label(label: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", label.strip())
    return safe or "object"


def extract_frame_from_pad(pad, buffer):
    fmt, width, height = get_caps_from_pad(pad)
    if not fmt or not width or not height:
        return None, None, None
    frame = get_numpy_from_buffer(buffer, fmt, width, height)
    return frame, width, height


def save_detection_crops(
    frame,
    width: int,
    height: int,
    detections,
    crop_dir: Path,
    frame_id: int,
    id_resolver=None,
):
    for idx, detection in enumerate(detections, start=1):
        bbox = detection.get_bbox() #what get the coordinate of the box
        label = safe_label(detection.get_label())
        track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
        if len(track) != 1:
            continue
        track_id = track[0].get_id()
        global_id = id_resolver(track_id, frame_id) if id_resolver else track_id

        x_min = int(max(0, bbox.xmin() * width))
        y_min = int(max(0, bbox.ymin() * height))
        x_max = int(min(width, (bbox.xmin() + bbox.width()) * width))
        y_max = int(min(height, (bbox.ymin() + bbox.height()) * height))

        if x_max <= x_min or y_max <= y_min:
            continue

        crop = frame[y_min:y_max, x_min:x_max]
        if crop.size == 0:
            continue

        class_dir = crop_dir / label
        track_dir = class_dir / f"id_{global_id}"
        track_dir.mkdir(parents=True, exist_ok=True)
        filename = f"frame_{frame_id:06d}_{idx:02d}.jpg"
        cv2.imwrite(str(track_dir / filename), crop)
