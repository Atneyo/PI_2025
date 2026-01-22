# Monitoring

## Overview

This repository contains scripts for monitoring various aspects of a Raspberry Pi.

Currently supported monitoring types:

* **Temperature monitoring**
* **Memory monitoring**
* **Camera detection**
* **Hailo detection**

Each file provides functions that can be used to monitor different metrics on the Raspberry Pi.


## Prerequisites

It is recommended to use a Python virtual environment before running the scripts.  
For Linux environments, you can set up a virtual environment and install the required libraries as follows:

```bash
python3 -m venv env_name
source env_name/bin/activate
pip install -r requirements.txt
```

## Running the Monitoring Scripts

After setting up the environment and installing the dependencies, you can run the monitoring scripts as follows (on Linux):

```bash
python3 temperature_monitoring.py
```

For energy monitoring you need to change line 26 of `energy_monitoring.py` file to use it without docker.

With Docker:
```
cmd = [
        "/usr/local/bin/joularcore",
        "-f", CSV_FILE   #-f option to enable writing to a given csv output
    ]
```

Without Docker:
```
cmd = [
        "sudo",
        "/usr/local/bin/joularcore",
        "-f", CSV_FILE   #-f option to enable writing to a given csv output
    ]
```