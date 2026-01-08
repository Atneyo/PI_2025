import subprocess
import signal
import time
import csv
import json
import platform
import datetime
import logging
import tempfile
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

CSV_FILE = "energy_global.csv"
JSON_FILE = "energy_log.json"
INTERVAL = 10  #in seconds

process = None


def start_energy_monitoring():
    global process

    logging.info("Starting GLOBAL energy monitoring")

    cmd = [
        "sudo", "/joularcore/target/release/joularcore",################# CHANGE THE PATH TO THE FULL PATH TO JOULARCORE ####################################
        "-f", CSV_FILE   #-f option to enable writing to a given csv output
    ]

    process=subprocess.Popen(
        cmd
    )


def stop_energy_monitoring():
    global process

    logging.info("Stopping energy monitoring")

    if process is not None:
        process.send_signal(signal.SIGINT)
        process.wait()


def get_latest_energy_row():
    ##Reads the last row of the PowerJoular CSV file, returns None if file is missing or empty.
    if not os.path.exists(CSV_FILE):
        return None

    try:
        with open(CSV_FILE, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if not rows:
                return None
            return rows[-1]
    except Exception:
        logging.exception("Failed to read energy CSV")
        return None


def get_energy_info():
    energy_row = get_latest_energy_row()
    if energy_row is None:
        return None

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "system": platform.system(),
        "machine": platform.machine(),
        "energy": energy_row
    }


def save_to_json(filename, data):
    #Append atomically to a JSON file (stored as a list).

    try:
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    json_data = json.load(f)
            except (json.JSONDecodeError, PermissionError):
                json_data = []
        else:
            json_data = []

        json_data.append(data)

        dirn = os.path.dirname(os.path.abspath(filename)) or "."
        with tempfile.NamedTemporaryFile("w", dir=dirn, delete=False) as tf:
            json.dump(json_data, tf, indent=4)
            tmpname = tf.name

        os.replace(tmpname, filename)

    except Exception:
        logging.exception("Failed to write to %s", filename)



if __name__ == "__main__":
    start_energy_monitoring()

    try:
        while True:
            energy_info = get_energy_info()
            if energy_info:
                save_to_json(JSON_FILE, energy_info)
                logging.info("Saved energy information")
            else:
                logging.warning("No energy data available yet")

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        logging.info("Exiting on user interrupt")

    except Exception:
        logging.exception("Unhandled exception in main loop")

    finally:
        stop_energy_monitoring()
