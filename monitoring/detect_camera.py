import pyudev
import subprocess
import shutil
import datetime
import re

from global_monitoring_functions import save_cur_stats_json, save_to_json, glob_filename

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
    if shutil.which('rpicam-hello'):
        try:
            result = subprocess.run(
                ['rpicam-hello', '--list-cameras'],
                capture_output=True,
                text=True,
                timeout=3,
            )
            out = result.stdout.strip()
            if result.returncode == 0 and out:
                for line in out.splitlines():
                    if re.match(r'^\s*\d+\s*:', line):
                        name = line.split(':', 1)[1].strip() or "Raspberry Pi Camera"
                        cameras.append({"device_node": "/dev/video0", "name": name})
                        break
                return cameras
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        except FileNotFoundError:
            pass

    return cameras

def detect_all_cameras():
    cameras = list_usb_cameras()
    cameras.extend(list_rpi_cameras())
    return cameras

def get_cur_camera_presence():
    Rpi_cameras = list_rpi_cameras()!=[]
    Usb_cameras = list_usb_cameras()!=[]
    data ={
        "timestamp" : datetime.datetime.now().isoformat(),
        "cameras": {
            "Rpi_cameras" : Rpi_cameras,
            "Usb_cameras": Usb_cameras
        }
    }
    return data



if __name__ == "__main__":
    cams = detect_all_cameras()
    data = get_cur_camera_presence()
    save_cur_stats_json(glob_filename,data)
    for cam in cams:
        print(f"Camera: {cam.get('name', 'Unknown')}")
        print(f"Device: {cam.get('device_node', 'N/A')}")
        print()
