import pyudev
import subprocess

def list_usb_cameras():
    context = pyudev.Context()
    cameras = []
    for device in context.list_devices(subsystem='video4linux'):
        parent = device.find_parent('usb', 'usb_device')
        if parent is None:
            continue

        cameras.append({
            "device_node": device.device_node,  #/dev/video* 
            "name": parent.get('ID_MODEL_FROM_DATABASE') or parent.get('ID_MODEL')
        })

    return cameras

def list_rpi_cameras():
    cameras = []
    try:
        result = subprocess.run(['vcgencmd', 'get_camera'], capture_output=True, text=True)
        output = result.stdout.strip()
        if 'supported=1' in output and 'detected=1' in output:
            cameras.append({
                "device_node": "/dev/video0",
                "name": "Raspberry Pi Camera"
            })
    except FileNotFoundError:
        pass

    return cameras

def detect_all_cameras():
    cameras = list_usb_cameras()
    cameras.extend(list_rpi_cameras())
    return cameras


if __name__ == "__main__":
    cams = detect_all_cameras()
    for cam in cams:
        print(f"Camera: {cam.get('name', 'Unknown')}")
        print(f"Device: {cam.get('device_node', 'N/A')}")
        print()
