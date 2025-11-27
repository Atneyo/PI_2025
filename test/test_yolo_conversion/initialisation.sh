#!/bin/bash

echo "=============================="
echo "   CHECK 0 : OS VERSION"
echo "=============================="
uname -a
cat /etc/os-release

### ----------------------------------------------------------
### 1) UPDATE SYSTEM
### ----------------------------------------------------------

echo "[1] Updating system..."
sudo apt update && sudo apt upgrade -y

### ----------------------------------------------------------
### 2) INSTALL CAMERA SUPPORT + TEST
### ----------------------------------------------------------

echo "[2] Installing camera support..."
sudo apt install -y python3-picamera2 libcamera-apps v4l-utils

echo "Listing cameras..."
libcamera-hello --list-cameras

echo "Running a 5-second camera test..."
libcamera-hello --nopreview -t 5000

### ----------------------------------------------------------
### 3) INSTALL BASIC PYTHON LIBS
### ----------------------------------------------------------

echo "[3] Installing Python essentials..."
sudo apt install -y python3-pip python3-venv python3-opencv

pip install --upgrade pip
pip install numpy matplotlib pillow requests tqdm

python3 - << 'EOF'
print("==============================")
print("TEST PYTHON BASICS")
print("==============================")
import cv2, numpy as np
img = np.zeros((200,200,3), dtype=np.uint8)
cv2.imwrite("test_image.png", img)
print("OK : numpy + opencv working, image saved -> test_image.png")
EOF

### ----------------------------------------------------------
### 4) INSTALL HAILO TOOLCHAIN
### ----------------------------------------------------------

echo "[4] Installing Hailo packages..."

# ---- change the version if needed ----
HAILO_DEB="hailo-all_4.17.0_arm64.deb"

if [ ! -f "$HAILO_DEB" ]; then
    echo "ERROR: $HAILO_DEB missing"
    echo "Download from: https://hailo.ai/developer-zone/software-downloads/"
    exit 1
fi

sudo dpkg -i $HAILO_DEB || sudo apt --fix-broken install -y

### ----------------------------------------------------------
### 5) TEST HAILO DEVICE
### ----------------------------------------------------------

echo "[5] Testing Hailo device..."
hailo_device.py || true
hailo_device_monitor.py || true

echo "Running basic Hailo test inference..."
hailo_cli run \
    --hef /usr/lib/hailo/examples/hef/person_detection.hef \
    --input /usr/lib/hailo/examples/images/people.jpg

### ----------------------------------------------------------
### 6) INSTALL HAILORT + TAPPAS
### ----------------------------------------------------------

echo "[6] Installing HailoRT + TAPPAS Python bindings..."
pip install hailo_sdk_client
pip install hailo_ai
pip install hailo_tappas

python3 - << 'EOF'
print("==============================")
print("TEST HAILORT PYTHON")
print("==============================")
from hailo_platform import Device
d = Device()
print("OK : HailoRT python device opened")
EOF

### ----------------------------------------------------------
### 7) INSTALL YOLO TOOLCHAIN (Ultralytics)
### ----------------------------------------------------------

echo "[7] Installing YOLO11 python package..."
pip install ultralytics

python3 - << 'EOF'
from ultralytics import YOLO
print("Loading YOLO11n model...")
model = YOLO("yolo11n.pt")
print("Model loaded. OK")
EOF

### ----------------------------------------------------------
### 8) (OPTIONAL) CONVERT YOLO → HAILO
### ----------------------------------------------------------

echo "[8] READY FOR YOLO → HAILO CONVERSION"
echo "Use: hailo_model_converter --help"
echo "Example:"
echo "hailo_model_converter --model-path yolo11n.onnx --yaml-path yolo11n.yaml --hw-arch hailo8"
echo ""
echo "Pipeline complete!"
