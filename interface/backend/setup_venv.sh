#!/usr/bin/env bash

set -euo pipefail

# Resolve paths relative to this script so it runs from anywhere
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
PYTHON_BIN="${PYTHON_BIN:-python3}"

declare -A MANUAL_HINTS=(
  ["apt-listchanges==4.8"]="sudo apt-get install apt-listchanges"
  ["cloud-init==25.2"]="sudo apt-get install cloud-init"
  ["cupshelpers==1.0"]="sudo apt-get install system-config-printer"
  ["dbus-python==1.4.0"]="sudo apt-get install python3-dbus libdbus-1-dev libglib2.0-dev"
  ["hailo-tappas-core-python-binding==5.1.0"]="Install via Hailo TAPPAS SDK (not on PyPI)"
  ["hailort==4.23.0"]="Install via HailoRT SDK (not on PyPI)"
  ["opencv==4.10.0"]="Use opencv-python or build OpenCV manually; base package not on PyPI"
  ["Mako==1.3.9.dev0"]="Pin to a released version (dev build missing on PyPI)"
  ["OpenEXR==1.3.10"]="Use openexr Python bindings from PyPI or build OpenEXR manually"
  ["PyQt5==5.15.11"]="Install via apt (python3-pyqt5) or ensure Qt/qmake dev tools are available"
  ["pysmbc==1.0.25.1"]="Install libsmbclient-dev and python3-smbc via apt"
  ["lgpio==0.2.2.0"]="sudo apt-get install python3-lgpio swig"
  ["rpi-lgpio==0.6"]="sudo apt-get install python3-lgpio"
  ["pycups==2.0.4"]="sudo apt-get install libcups2-dev python3-cups"
  ["RTIMULib==7.2.1"]="sudo apt-get install python3-rtimulib"
  ["python-apt==3.0.0"]="sudo apt-get install python3-apt"
  ["rpi-keyboard-config==1.0"]="sudo apt-get install rpi-keyboard-config"
  ["smbus==1.1"]="sudo apt-get install python3-smbus"
  ["ssh-import-id==5.10"]="sudo apt-get install ssh-import-id"
  ["videodev2==0.0.4"]="sudo apt-get install python3-videodev"
)

if [[ ! -f "$REQ_FILE" ]]; then
  echo "requirements.txt not found at $REQ_FILE" >&2
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi
HOST_PYTHON_BIN="$(command -v "$PYTHON_BIN")"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Virtual environment not found. Creating venv at $VENV_DIR"
  mkdir -p "$(dirname "$VENV_DIR")"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
elif [[ ! -f "$VENV_DIR/bin/activate" ]]; then
  echo "Virtual environment directory exists but is incomplete. Recreating it."
  rm -rf "$VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "Virtual environment already exists in $VENV_DIR"
fi

# Activate the venv to drive all installs through it
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

# Always refresh pip/setuptools/wheel so later installs succeed
python -m pip install --upgrade pip setuptools wheel

# Build a temp requirements file that strips system-only packages
TMP_REQ="$(mktemp)"
trap 'rm -f "$TMP_REQ"' EXIT
SKIPPED_PKGS=()

while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
  line="$(printf '%s' "$raw_line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  if [[ -z "$line" || "${line:0:1}" == "#" ]]; then
    printf '%s\n' "$raw_line" >> "$TMP_REQ"
    continue
  fi

  if [[ -n "${MANUAL_HINTS[$line]:-}" ]]; then
    printf 'Skipping %s (install manually with: %s)\n' "$line" "${MANUAL_HINTS[$line]}"
    SKIPPED_PKGS+=("$line")
    continue
  fi

  # types-* wheels are published with timestamps; install best available directly
  if [[ "$line" =~ ^(types-[[:alnum:]._-]+)==(.+)$ ]]; then
    pkg_name="${BASH_REMATCH[1]}"
    requested_version="${BASH_REMATCH[2]}"
    printf 'Installing %s (latest available instead of %s)...\n' "$pkg_name" "$requested_version"
    if python -m pip install "$pkg_name"; then
      continue
    else
      echo "Failed to install $pkg_name (requested $requested_version)" >&2
      exit 1
    fi
  fi

  printf '%s\n' "$raw_line" >> "$TMP_REQ"
done < "$REQ_FILE"

echo "Installing Python packages from requirements.txt (OS-only packages skipped)..."
python -m pip install -r "$TMP_REQ"

# Detect system-wide Hailo SDK bindings and expose them inside the venv via .pth
SYSTEM_HAILO_MODULES=("hailo" "hailort")
HAILO_PATHS=()
for module in "${SYSTEM_HAILO_MODULES[@]}"; do
  MODULE_DIR="$("$HOST_PYTHON_BIN" - <<PY || true
import importlib.util, os
spec = importlib.util.find_spec("$module")
if spec and spec.origin:
    path = spec.submodule_search_locations[0] if spec.submodule_search_locations else os.path.dirname(spec.origin)
    print(path)
PY
)"
  if [[ -n "$MODULE_DIR" && -d "$MODULE_DIR" && "$MODULE_DIR" != *"$VENV_DIR"* ]]; then
    echo "Found system $module module at $MODULE_DIR"
    HAILO_PATHS+=("$MODULE_DIR")
  fi
done

if [[ ${#HAILO_PATHS[@]} -gt 0 ]]; then
  SITE_PACKAGES="$(python - <<'PY'
import site
print(site.getsitepackages()[0])
PY
)"
  PTH_FILE="$SITE_PACKAGES/hailo_sdk_paths.pth"
  : > "$PTH_FILE"
  declare -A SEEN_PATHS=()
  for path in "${HAILO_PATHS[@]}"; do
    if [[ -z "${SEEN_PATHS[$path]:-}" ]]; then
      printf '%s\n' "$path" >> "$PTH_FILE"
      SEEN_PATHS[$path]=1
    fi
  done
  echo "Linked system Hailo SDK modules via $PTH_FILE"
else
  echo "System Hailo SDK modules not found. Install HailoRT/TAPPAS if you need hailo bindings."
fi

if [[ ${#MANUAL_HINTS[@]} -gt 0 ]]; then
  echo
  echo "Install the skipped system packages manually if you need them:"
  if [[ ${#SKIPPED_PKGS[@]} -gt 0 ]]; then
    for pkg in "${SKIPPED_PKGS[@]}"; do
      printf '  - %-25s -> %s\n' "$pkg" "${MANUAL_HINTS[$pkg]}"
    done
  else
    for pkg in "${!MANUAL_HINTS[@]}"; do
      printf '  - %-25s -> %s\n' "$pkg" "${MANUAL_HINTS[$pkg]}"
    done
  fi
fi

echo
echo "Done. Activate the virtual environment with:"
echo "  source \"$VENV_DIR/bin/activate\""
