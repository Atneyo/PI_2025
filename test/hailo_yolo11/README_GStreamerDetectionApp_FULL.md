
# GStreamerDetectionApp – How does the detection pipeline work.

This document describes exactly what can be configured, how it works internally,
and how to control behavior (FPS, source, inference, tracking) for Hailo-based
pipelines using either webcams or video files.

---

## 1. Overview

This application builds and runs a GStreamer pipeline for real-time AI inference
using:

- Hailo hardware accelerators
- Compiled Hailo models (.hef)
- Native post-processing shared libraries (.so)
- Optional object tracking
- Optional user callbacks
- Display, file output, or streaming sinks

The pipeline is built as a string and executed by GStreamer.

---

## 2. Class Architecture

```
GStreamerApp                (base framework)
└── GStreamerDetectionApp   (application-specific pipeline)
```

- `GStreamerApp` handles CLI parsing, lifecycle management, and the GStreamer main loop.
- `GStreamerDetectionApp` defines the concrete detection pipeline.

---

## 3. Core Function: get_pipeline_string

### Signature

```python
def get_pipeline_string(self) -> str
```

### Purpose

- Builds the full GStreamer pipeline description.
- Returns a pipeline string.
- Does not process frames directly.

This function is overridden by application-specific classes.

---

## 4.Pipeline Structure

```
SOURCE
 → videorate + capsfilter (FPS control)
 → inference (hailonet)
 → post-processing (.so)
 → tracker (optional)
 → user callback (optional)
 → display / sink
```

---

## 5. Source Pipeline

### Function

```python
SOURCE_PIPELINE(
    video_source,
    video_width,
    video_height,
    frame_rate,
    sync,
    video_format
)
```

### Supported Sources

| Source Type | Example |
|------------|---------|
| USB Webcam | /dev/video0 |
| Video File | /path/video.mp4 |
| RTSP | rtsp://... |
| Raspberry Pi Camera | appsrc |

Source type is automatically detected.

---

## 6. FPS Control (Exact)

### Implementation

The source pipeline always includes:

```
videorate name=source_videorate
capsfilter name=source_fps_caps caps="video/x-raw,framerate=X/1"
```

This guarantees exact framerate enforcement by dropping excess frames.

---

### How FPS Is Selected

1. User provides `--frame-rate`
2. Stored in `self.frame_rate`
3. Applied via videorate + capsfilter
4. Output FPS is exact

---

### Mandatory Condition

FPS limiting is applied only when:

```
sync == "true"
```

Default behavior:

| Source | sync | FPS limited |
|--------|------|------------|
| Video file | true | Yes |
| Webcam | false | No |
| RTSP | false | No |

To force FPS limiting on webcams or RTSP streams, set sync to true.

---

### Runtime FPS Update

FPS can be changed dynamically without restarting the pipeline:

```python
app.update_fps_caps(new_fps=5)
```

---

## 7. Inference Pipeline (Hailo)

### Function

```python
INFERENCE_PIPELINE(
    hef_path,
    post_process_so,
    batch_size,
    config_json,
    post_function_name,
    additional_params
)
```

### Mandatory Parameters

| Parameter | Description |
|----------|-------------|
| hef_path | Path to .hef model |
| batch_size | Frames per inference |
| post_process_so | Post-processing library |
| post_function_name | Function inside the .so |

---

## 8. Tracking

### Function

```python
TRACKER_PIPELINE(class_id=1)
```

Tracks objects across frames using Kalman filtering.

---

## 9. User Callback

### Function

```python
USER_CALLBACK_PIPELINE()
```

Allows injection of custom logic via pad probes.

---

## 10. Display Pipeline

### Function

```python
DISPLAY_PIPELINE(
    video_sink,
    sync,
    show_fps
)
```

Supports overlays and FPS visualization.

---

## 11. Webcam vs Video File Behavior

| Feature | Webcam | Video File |
|--------|--------|------------|
| FPS default | Native camera FPS | File timestamps |
| FPS forced | Yes (sync=true) | Yes |
| Looping | No | Yes |
| Latency | Low | Deterministic |

---

## 12. Recommended Configurations

### Stable 5 FPS (Any Source)

```bash
--frame-rate 5
--force-sync
--show-fps
```

### Unlimited FPS

```bash
--disable-sync
```

---

## 13. Key Takeaways

- FPS is strictly enforced using videorate and capsfilter.
- Hailo inference runs only on selected frames.
- Webcam and file sources behave differently unless sync is forced.
- The pipeline is modular, deterministic, and suitable for embedded AI deployment.
