import json
import time
import datetime
import os
import glob
import statistics
import logging

from global_monitoring_functions import save_cur_stats_json, save_to_json, glob_filename

#ensure psutil name exists even if import fails
psutil = None
try:
    import psutil as _psutil
    psutil = _psutil
except Exception:
    psutil = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

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

#Boolean variable initialisation (for hailo presence)
try:
    from hailort import Device
    HAILO = True
except ImportError:
    HAILO = False

file = "temp_stats.json"

#simple validation params  can be modified as needed
_TEMP_MIN = -20.0
_TEMP_MAX = 125.0
_SENTINELS = {0, -1, 32768, 85, 255, 65535}

#Function to get cpu temperature
def _read_temp(path):
    try:
        with open(path, 'r') as f:
            raw = f.read().strip()
        if not raw:
            return None
        v = float(raw)
        #convert millidegree values (common) to °C
        if abs(v) > 1000:
            v = v / 1000.0
        return v
    except Exception:
        return None


def _valid_temp(v):
    try:
        if v is None:
            return False
        if int(v) in _SENTINELS:
            return False
        return _TEMP_MIN <= float(v) <= _TEMP_MAX
    except Exception:
        return False


def get_cpu_temp():
    """Minimal robust CPU temp: scan sysfs, normalize, validate, small retry, fallback to psutil."""
    temps = []
    #check temperature multiple times to avoid momentary read glitches
    for _ in range(2):
        for p in sorted(glob.glob('/sys/class/thermal/thermal_zone*/temp')):
            v = _read_temp(p)
            if _valid_temp(v):
                temps.append(v)
        if temps:
            #use first temps found
            break
        time.sleep(0.05)

    #fallback to hwmon style paths (if nothing is found in the thermal_zone paths)
    if not temps:
        for p in sorted(glob.glob('/sys/class/thermal/*/hwmon*/temp*_input')):
            v = _read_temp(p)
            if _valid_temp(v):
                temps.append(v)
        if temps:
            #use first hwmon readings
            pass

    #fallback to psutil if nothing found
    if not temps and psutil is not None:
        try:
            pts = psutil.sensors_temperatures()
            for name, entries in pts.items():
                for e in entries:
                    try:
                        v = float(e.current)
                        if _valid_temp(v):
                            temps.append(v)
                    except Exception:
                        continue
        except Exception:
            pass

    if not temps:
        logging.warning('No valid temperature readings found')
        return None

    med = statistics.median(temps)
    logging.info('Temperature candidates=%s median=%.2f°C', temps, med)
    return round(med, 2)

#Function to get the Hailo hat temperature 
def get_hailo_temperature():
    if not HAILO:
        return None

    try:
        with Device() as device:
            return device.get_chip_temperature()
    except:
        return None
    

def get_temp_info():
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "cpu_temperature_c": get_cpu_temp(),
        "hailo_temperature_c": get_hailo_temperature()
    }
    return data

def get_temp_data_for_cur_log(data):
    data_part={
        "timestamp" : datetime.datetime.now().isoformat(),
        "temperature": {
            "cpu_temperature_c": data["cpu_temperature_c"],
            "hailo_temperature_c": data["hailo_temperature_c"]
        }
    }
    return data_part



if __name__ == "__main__":
    print(f"Raspberry Pi: {is_raspberry_pi()}")
    print(f"Hailo available: {HAILO}")
    while True:
        data = get_temp_info()
        data_cur = get_temp_data_for_cur_log(data)
        save_to_json(file,data)
        save_cur_stats_json(glob_filename,data_cur)
        time.sleep(5)
