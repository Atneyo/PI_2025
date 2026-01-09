import datetime

from global_monitoring_functions import save_cur_stats_json, save_to_json, glob_filename

def is_hailo_hat_present():
    try:
        from hailort import Device
        HAILO = True
    except ImportError:
        HAILO = False
    return HAILO


def get_cur_hailo_presence():
    data ={
        "timestamp" : datetime.datetime.now().isoformat(),
        "hailo_presence": is_hailo_hat_present()
    }
    return data

if __name__ == "__main__":
    data = get_cur_hailo_presence()
    save_cur_stats_json(glob_filename, data)
    if is_hailo_hat_present():
        print("Hailo HAT is present.")
    else:
        print("Hailo HAT is not present.")