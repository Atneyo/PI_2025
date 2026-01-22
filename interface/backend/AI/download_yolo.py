from __future__ import annotations

from datetime import datetime
from pathlib import Path


def recording_output_path(
    record_filename: str | None,
    output_dir: str | Path | None,
    recordings_dir: Path,
) -> Path:
    """Ensure the recordings directory exists and return the selected file path."""
    base_dir = Path(output_dir) if output_dir is not None else recordings_dir
    base_dir.mkdir(parents=True, exist_ok=True)
    if record_filename:
        candidate = Path(record_filename)
        if candidate.is_absolute():
            return candidate
        return (base_dir / candidate).resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (base_dir / f"detections_{timestamp}.mkv").resolve()


def temporary_recording_path(target_path: Path) -> Path:
    """Return the `.part` file used while the pipeline is still running."""
    return target_path.with_name(f"{target_path.name}.part")


def crop_output_dir(output_dir: str | Path | None, recordings_dir: Path) -> Path:
    base_dir = Path(output_dir) if output_dir is not None else recordings_dir
    crops_dir = base_dir / "box_cropping_"
    crops_dir.mkdir(parents=True, exist_ok=True)
    return crops_dir
