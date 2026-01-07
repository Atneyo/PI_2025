# YOLO Detection Helper

This folder exposes a single entry point `yolo_detection.py` and splits the logic into smaller modules to keep the code readable and maintainable.

## File layout

- `yolo_detection.py`: main entry point, orchestration, `yolo_detection(...)` API.
- `gstreamer_yolo.py`: GStreamer pipeline construction + `RecordingDetectionApp` class.
- `cropping_yolo.py`: frame extraction and crop saving.
- `stats_yolo.py`: stats collection, session summary, JSON export.
- `download_yolo.py`: output paths, `.part` temp file, crops folder.
- `yolov11n.hef`: default Hailo model.

## Pipeline flow

Fixed GStreamer block order:

1. `SOURCE_PIPELINE` reads the source (file or webcam).
2. `INFERENCE_PIPELINE` + wrapper run Hailo detection.
3. `TRACKER_PIPELINE` applies tracking.
4. `USER_CALLBACK_PIPELINE` triggers `app_callback` for stats + crops.
5. `_record_video_branch()` applies overlay then encodes to `matroskamux -> filesink`.

Display mode was removed: the pipeline records only, which allows faster-than-realtime processing.

## Outputs

For a given `record_filename` (e.g. `result.webm`):

- Video: `outputs/result.webm`
- Summary JSON: `outputs/result.json`
- Crops: `outputs/box_cropping_/<class>/id_<global_id>/frame_XXXXXX_YY.jpg`

Crops are only saved when a tracking ID exists (metadata `HAILO_UNIQUE_ID`),  
and they are organized by class then tracking ID for clarity.

## Usage

```python
from interface.backend.AI.yolo_detection import yolo_detection

result_path = yolo_detection(
    live_input=False,
    video_path="uploads/video.mp4",
    frame_rate=15,
    hef_path="interface/backend/AI/yolov11n.hef",
    output_dir="interface/backend/outputs",
    record_filename="result.webm",
)
print("Fichier annote :", result_path)
```

## Common tweaks

- Default source: change `USE_WEBCAM` or `DEFAULT_VIDEO` in `yolo_detection.py`.
- FPS / HEF: change `FRAME_RATE` / `HEF_FILE` or pass `frame_rate=` / `hef_path=`.
- Output folder/name: pass `output_dir=` and `record_filename=`.
- Disable recording: `enable_recording=False` (useful for pipeline debugging).

## Notes

- Recording writes to `.part` first, then renames at the end of the pipeline.
- The summary JSON is created next to the video.

## Run without the backend

You can also run the detection directly from the CLI without starting FastAPI. From the repo root, open a Python shell and call the function with a video path:

for vidéo : 

```bash
python - <<'PY'
from interface.backend.AI.yolo_detection import yolo_detection

result = yolo_detection(
    live_input=False,
    video_path="path/to/video.mp4",
    output_dir="interface/backend/outputs/<video_name>",
    record_filename="result.webm",
)
print("Output:", result)
PY
```

for webcam:
```bash
python - <<'PY'
from interface.backend.AI.yolo_detection import yolo_detection
yolo_detection(live_input=True, output_dir="interface/backend/outputs/webcam")
print("Output:", result)
PY
```
