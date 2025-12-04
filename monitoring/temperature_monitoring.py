import json
import time
import datetime
import os
try:
    import psutil
except ImportError:
    pass

#checking if the device the monitoring is used on is an rpi5
def is_raspberry_pi():
    try:
        with open("/sys/firmware/devicetree/base/model", "r") as f:
            if "raspberry pi" in f.read().lower():
                return True
    except:
        pass
    try:
        with open("/proc/cpuinfo") as f:
            c = f.read().lower()
            if "bcm27" in c or "raspberry pi" in c:
                return True
    except:
        pass

    return False

#Boolean ariable initialisation (for hailo presence)
try:
    from hailort import Device
    HAILO = True
except ImportError:
    HAILO = False

file = "temp_stats.json"

#Function 
def get_cpu_temp():
    pi_temp_path = "/sys/class/thermal/thermal/zone0/temp"
    if os.path.exists(pi_temp_path):
        try:
            with open(pi_temp_path, "r") as f:
                return int(f.read().strip()) / 1000.0
        except:
            pass

    if not is_raspberry_pi():
        try:
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                if entries:
                    return entries[0].current
        except:
            pass

    return None

def get_hailo_temperature():
    if not HAILO:
        return None

    try:
        with Device() as device:
            return device.get_chip_temperature()
    except:
        return None

def write_stats():
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "cpu_temperature_c": get_cpu_temp(),
        "hailo_temperature_c": get_hailo_temperature()
    }

    # Append mode JSON list
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([data], f, indent=4)
    else:
        with open(file, "r+") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
            existing.append(data)
            f.seek(0)
            json.dump(existing, f, indent=4)

    print("Saved:", data)


if __name__ == "__main__":
    print(f"Raspberry Pi: {is_raspberry_pi()}")
    print(f"Hailo available: {HAILO}")
    while True:
        write_stats()
        time.sleep(5)