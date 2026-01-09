import psutil
import platform
import datetime
import time
import logging

from global_monitoring_functions import save_cur_stats_json, save_to_json, glob_filename

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


def current_mem_disk_stats(memory_info, disk_info):
    part_data={
        "timestamp" : datetime.datetime.now().isoformat(),
        "memory" : {
            "used_ram": memory_info["used_ram"],
            "ram_percent_used": memory_info["ram_percent_used"]

        },
        "swap":{
            "used_swap": memory_info["used_swap"],
            "swap_percent_used": memory_info["swap_percent_used"]
        },
        "storage" : {}
    }
    for mount, info in disk_info.items():
        part_data["storage"][mount] = {
            "used": info["used"],
            "percent_used": info["percent_used"]
        }
    return part_data





if __name__ == "__main__":
    try:
        while True:
            memory_info = get_memory_info()
            disk_info = get_disk_info()
            curr = current_mem_disk_stats(memory_info, disk_info)
            # separate files for clarity
            save_to_json("memory_log.json", memory_info)
            #print("Saved memory info:", memory_info)
            save_to_json("disk_log.json", {"timestamp": datetime.datetime.now().isoformat(), "disks": disk_info})
            #print("Saved disk info:", {"timestamp": datetime.datetime.now().isoformat(), "disks": disk_info})
            save_cur_stats_json(glob_filename,curr)
            #print("saved to curr file", {"timestamp": datetime.datetime.now().isoformat(), "data": curr})
            logging.info('Saved memory and disk stats')
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info('Exiting on user interrupt')
    except Exception:
        logging.exception('Unhandled exception in main loop')

