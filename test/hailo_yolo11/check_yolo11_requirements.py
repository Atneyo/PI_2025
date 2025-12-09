#!/usr/bin/env python3
"""
Quick dependency/configuration sanity check for yolo11_gstreamer.py.

Runs a series of light-weight checks (module imports, files on disk, CLI tools)
and prints actionable guidance when something is missing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import importlib
import shutil
import sys


@dataclass
class CheckResult:
    item: str
    success: bool
    message: str


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
HEF_FILE = ROOT / "yolov11n.hef"


def header(title: str) -> None:
    print(f"\n=== {title} ===")


def ok(item: str) -> CheckResult:
    return CheckResult(item=item, success=True, message="OK")


def fail(item: str, hint: str) -> CheckResult:
    return CheckResult(item=item, success=False, message=hint)


def check_gi() -> CheckResult:
    item = "PyGObject (gi/Gst)"
    try:
        gi = importlib.import_module("gi")
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst  # noqa: F401  # pylint: disable=import-outside-toplevel
    except Exception as exc:  # pylint: disable=broad-except
        hint = (
            f"{exc}\nInstall system packages: "
            "sudo apt install python3-gi python3-gi-cairo gir1.2-gstreamer-1.0 libgirepository1.0-dev"
        )
        return fail(item, hint)
    return ok(item)


def check_module(mod_name: str, friendly: str, install_hint: str) -> CheckResult:
    try:
        importlib.import_module(mod_name)
        return ok(friendly)
    except ImportError as exc:
        return fail(friendly, f"{exc}\n{install_hint}")


def check_binary(binary: str, friendly: str, install_hint: str) -> CheckResult:
    if shutil.which(binary):
        return ok(friendly)
    return fail(friendly, install_hint)


def check_file(path: Path, friendly: str, hint: str) -> CheckResult:
    if path.exists():
        return ok(friendly)
    return fail(friendly, hint.format(path=path))


def run_checks() -> list[CheckResult]:
    checks = [
        check_gi(),
        check_module(
            "hailo",
            "hailo (HailoRT Python bindings)",
            "Install the wheel that matches your platform (e.g. pip install hailort-4.23.0-*.whl).",
        ),
        check_module(
            "hailo_apps",
            "hailo_apps (tappas-core binding)",
            "Install hailo-apps/tappas-core: pip install tappas_core_python_binding-3.31.0-*.whl",
        ),
        check_module(
            "hailo_apps.hailo_app_python.apps.detection.detection_pipeline",
            "hailo_apps detection pipeline",
            "hailo-apps-infra is missing or outdated; reinstall it per README instructions.",
        ),
        check_binary(
            "gst-launch-1.0",
            "GStreamer runtime binaries",
            "Install GStreamer: sudo apt install gstreamer1.0-* (base, good, bad, ugly as needed).",
        ),
        check_file(
            ENV_FILE,
            ".env configuration file",
            "Missing {path}. Create it or run hailo-post-install to generate it.",
        ),
        check_file(
            HEF_FILE,
            "yolov11n.hef network file",
            "Missing {path}. Copy/compile the network file expected by yolo11_gstreamer.py.",
        ),
    ]
    return checks


def main() -> None:
    header("YOLO11 GStreamer dependency check")
    results = run_checks()

    missing = [r for r in results if not r.success]
    for result in results:
        status = "OK" if result.success else "MISSING"
        print(f"[{status:8}] {result.item}")
        if not result.success:
            print(f"          -> {result.message}")

    header("Summary")
    if not missing:
        print("All required modules/files appear to be present. You can run yolo11_gstreamer.py.")
        sys.exit(0)

    print(f"{len(missing)} item(s) missing. Install/fix the components listed above and retry.")
    sys.exit(1)


if __name__ == "__main__":
    main()
