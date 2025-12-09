import psutil
import json
import platform
import datetime
import time
import logging
import tempfile
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")



def get_disk_info():
    disk_info = {}
    partitions = psutil.disk_partitions()
    for p in partitions:
        #skip pseudo filesystems and non-device mounts
        if not (p.device and p.device.startswith('/dev/')):
            continue
        #exclude snap and other app-specific mounts
        if '/snap/' in p.mountpoint or p.mountpoint.startswith('/snap'):
            continue
        #only include top-level mounts (depth <= 1) to avoid per-app mounts
        try:
            depth = p.mountpoint.rstrip('/').count('/')
        except Exception:
            depth = 0
        if depth > 1:
            #skip mounts like /snap/<app>/...,/var/lib/...,/run/user/... etc.
            continue

        try:
            usage = psutil.disk_usage(p.mountpoint)
            disk_info[p.mountpoint] = {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent_used": usage.percent
            }
        except PermissionError:
            continue
    return disk_info


def get_memory_info():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "system": platform.system(),
        "machine": platform.machine(),
        "total_ram": mem.total,
        "available_ram": mem.available,
        "used_ram": mem.used,
        "free_ram": mem.free,
        "ram_percent_used": mem.percent,
        "total_swap": swap.total,
        "used_swap": swap.used,
        "free_swap": swap.free,
        "swap_percent_used": swap.percent
    }

def save_to_json(filename, data):
    #append atomically to JSON file (entries are stored as a list, creating file if needed))
    try:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    json_data = json.load(f)
            except (json.JSONDecodeError, PermissionError):
                json_data = []
        else:
            json_data = []

        json_data.append(data)

        dirn = os.path.dirname(os.path.abspath(filename)) or '.'
        with tempfile.NamedTemporaryFile('w', dir=dirn, delete=False) as tf:
            json.dump(json_data, tf, indent=4)
            tmpname = tf.name
        os.replace(tmpname, filename)
    except Exception:
        logging.exception('Failed to write to %s', filename)

if __name__ == "__main__":
    try:
        while True:
            memory_info = get_memory_info()
            disk_info = get_disk_info()
            # separate files for clarity
            save_to_json("memory_log.json", memory_info)
            print("Saved memory info:", memory_info)
            save_to_json("disk_log.json", {"timestamp": datetime.datetime.now().isoformat(), "disks": disk_info})
            print("Saved disk info:", {"timestamp": datetime.datetime.now().isoformat(), "disks": disk_info})
            logging.info('Saved memory and disk stats')
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info('Exiting on user interrupt')
    except Exception:
        logging.exception('Unhandled exception in main loop')

