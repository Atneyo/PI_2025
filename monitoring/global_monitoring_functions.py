import os
import json
import tempfile
import logging

glob_filename = "current_monitoring_data.json"

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

def save_cur_stats_json(filename,data):
    try:
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    current = json.load(f)
            except (json.JSONDecodeError, PermissionError):
                current = {}
        else:
            current = {}

        #data not deleted but replaced here
        current.update(data)

        dirn = os.path.dirname(os.path.abspath(filename)) or "."
        with tempfile.NamedTemporaryFile("w", dir=dirn, delete=False) as tf:
            json.dump(current, tf, indent=4)
            tmpname = tf.name

        os.replace(tmpname, filename)

    except Exception:
        logging.exception("Failed to update snapshot %s", filename)