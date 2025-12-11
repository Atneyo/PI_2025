
def is_hailo_hat_present():
    try:
        from hailort import Device
        HAILO = True
    except ImportError:
        HAILO = False
    return HAILO

if __name__ == "__main__":
    if is_hailo_hat_present():
        print("Hailo HAT is present.")
    else:
        print("Hailo HAT is not present.")