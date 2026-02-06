from detect_camera import get_cur_camera_presence
from detect_hailo import get_cur_hailo_presence
from energy_monitoring import *
from temperature_monitoring import get_temp_info, get_temp_data_for_cur_log, file
from memory_monitoring import get_disk_info, get_memory_info, current_mem_disk_stats
from global_monitoring_functions import *
import time


start_energy_monitoring()
time.sleep(10)
try:
    while True:
        #energy
        energy_info = get_energy_info()
        cur_energy_info = get_energy_data_for_cur_log(energy_info)
        #camera
        cam_presence=get_cur_camera_presence()
        #hailo
        hailo_presence = get_cur_hailo_presence()
        #temperature
        temp_data = get_temp_info()
        cur_temp_data = get_temp_data_for_cur_log(temp_data)
        #memory
        disk_data = get_disk_info()
        mem_data = get_memory_info()
        cur_mem_disk_data=current_mem_disk_stats(mem_data,disk_data)

        #energy
        if energy_info:
            save_to_json(JSON_FILE, energy_info)
            save_cur_stats_json(glob_filename,cur_energy_info)
            logging.info("Saved energy information")
        else:
            logging.warning("No energy data available yet")
        # camera
        save_cur_stats_json(glob_filename, cam_presence)
        logging.info("Saved camera presence information")
        #hailo
        save_cur_stats_json(glob_filename, hailo_presence)
        logging.info("Saved hailo presence information")
        #temperature
        if temp_data:
            save_to_json(JSON_FILE, temp_data)
            save_cur_stats_json(glob_filename,cur_temp_data)
            logging.info("Saved temperature information")
        else:
            logging.warning("No temperature data available yet")
        #memory
        if disk_data and mem_data:
            save_to_json("disk_log.json", {"timestamp": datetime.datetime.now().isoformat(), "disks": disk_data})
            save_to_json("memory_log.json", mem_data)
            save_cur_stats_json(glob_filename, cur_mem_disk_data)
            logging.info("Saved memory information")
        else:
            logging.warning("No memory data available yet")

        time.sleep(glob_interval)

except KeyboardInterrupt:
    logging.info("Exiting on user interrupt")

except Exception:
    logging.exception("Unhandled exception in main loop")

finally:
    stop_energy_monitoring()