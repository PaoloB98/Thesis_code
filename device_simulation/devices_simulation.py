#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 28 10:26:11 2022

@author: Paolo Bono
"""

import os
import signal
from subprocess import Popen

import requests
from numpy import random
from typing import List
import time
import pandas as pd
from datetime import datetime
import sys
import pause


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Device:
    pid: int = -1
    dev_imsi: str = "imsi-208930000000"
                   #"imsi-208930000000000"
    dev_log: str = ""
    dev_config_file: str = ""

    def __init__(self, dev_imsi, dev_config, dev_log):
        self.pid = -1
        self.dev_imsi = dev_imsi
        self.dev_config_file = dev_config
        self.dev_log = dev_log

    def set_pid(self, pid):
        self.pid = pid

    def remove_pid(self):
        self.pid = -1


# Configuration
time_sleep_sec = 10.0
debug: int = 1
max_devices: int = 1000
deploy = False
initial_delay = time_sleep_sec*2.5
##############

device_list: List[Device] = []
last_activated_device = max_devices-1
connected_devices_num = 0
mean_conn_dev = [4, 2, 3, 2, 3, 2, 3, 5, 2, 7, 8, 9, 9, 10, 12, 10, 10, 11, 11, 12, 12, 12, 8, 5]
i = 0
iteration = 1
history_file = None
starting_val: pd.Series

exec_location = ["/home/paolo/Coding/UERANSIM/build/nr-ue", "/home/paolo/Coding/UERANSIM/build/nr-cli"]
arguments = sys.argv[1:]
if len(arguments) > 0:
    if arguments[0] == "-d":
        exec_location = ["/UERANSIM/build/nr-ue", "/UERANSIM/build/nr-cli"]
        deploy = True


def on_start():
    for i in range(0, max_devices):
        dev_name, dev_conf, dev_log = get_dev_conf_log_names(i)
        device_list.append(Device(dev_imsi=dev_name, dev_config=dev_conf, dev_log=dev_log))

    signal.signal(signal.SIGTERM, on_close)
    signal.signal(signal.SIGINT, on_close)
    signal.signal(signal.SIGHUP, on_close)

    if os.path.exists("./logs"):
        if not (os.path.isdir("./logs")):
            os.remove("./logs")
            os.mkdir("./logs")
    else:
        os.mkdir("./logs")


def sync_clock():
    if (deploy):
        address = "prom.free5gc.org:9090"
    else:
        address = "localhost:9089"
    protocol = "http://"
    scraping_API = protocol + address + "/api/v1/query?query=free5gc_core_connected_3gpp_ues[3m]"
    i = 0

    time_sec = time.time()
    while i < 10:
        try:
            response = requests.get(scraping_API)
        except:
            print("Something went wrong!")
            return time_sec
        rsp_json = response.json()

        if "result" in rsp_json['data']:
            result = rsp_json['data']['result']
            if "values" in result[0]:
                last_position = len(result[0]["values"])
                time_sec = result[0]["values"][last_position-1][0]
            break
        else:
            time.sleep(1)
        i = i + 1
    return time_sec + 1 / 10 * time_sleep_sec


def on_close(sig, frame):
    remove_device(connected_devices_num, connected_devices_num)
    print("Closing...\n")
    history_file.close()
    exit(0)


def add_device(actual_dev: int, num_to_add):
    global last_activated_device
    for iter in range(0, num_to_add):
        position = device_position_to_add()
        last_activated_device = position

        device = device_list[position]

        dev_std_out = open(device.dev_log, 'w+')
        # Popen(["/home/paolo/code/UERANSIM/build/nr-ue", "-c", config_name])
        proc_id = Popen([exec_location[0], "-c", device.dev_config_file], stdout=dev_std_out,
                        stderr=dev_std_out, shell=False).pid
        #print("/home/paolo/code/UERANSIM/build/nr-ue" + " -c " + device.dev_config_file + "\n")
        device.set_pid(proc_id)
    return actual_dev + num_to_add


def remove_device(actual_dev: int, num_to_rem):
    if num_to_rem <= 0:
        return 0
    pause_time = (time_sleep_sec / 2) / num_to_rem
    for index in range(0, num_to_rem):
        position = device_position_to_remove(connected_devices_num - index)

        device = device_list[position]

        Popen([exec_location[1], device.dev_imsi, "-e", "deregister switch-off"])
        # print("/home/paolo/code/UERANSIM/build/nr-cli" + device.dev_imsi + " -e 'deregister switch-off'\n")
        time.sleep(pause_time)
        #try:
        #    os.kill(device.pid, signal.SIGTERM)
        #except ProcessLookupError:
        #    print(f"[{Colors.FAIL}{datetime.now()}] [ERR] Process {device.pid} not found!")
        device.remove_pid()
        assert (position >= 0)
    return actual_dev - num_to_rem


def parser(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


def get_starting_values():
    starting_values = pd.read_csv('starting_data.csv', usecols=['time', 'num_usr'], parse_dates=[0], index_col=0,
                                  date_parser=parser)

    return starting_values


def device_position_to_add():
    global last_activated_device
    length = len(device_list)
    if last_activated_device < length - 1:
        next_position = last_activated_device + 1
    else:
        next_position = 0
    return next_position


def device_position_to_remove(connected_dev_num):
    global last_activated_device
    length = len(device_list)
    differ = last_activated_device - (connected_dev_num - 1)
    if differ < 0:
        position_to_remove = length + differ
    else:
        position_to_remove = differ
    return position_to_remove


def get_dev_conf_log_names(position):
    dev_name = "imsi-208930000000"
    config_name = "config/free5gc-ue"
    log_name = "log"
    if position < 10:
        dev_name = dev_name + "00" + str(position)
        config_name = config_name + "00" + str(position) + ".yaml"
        log_name = "logs/log_00" + str(position) + ".txt"
    else:
        if position <= 99:
            dev_name = dev_name + "0" + str(position)
            config_name = config_name + "0" + str(position) + ".yaml"
            log_name = "logs/log_0" + str(position) + ".txt"
        else:
            dev_name = dev_name + str(position)
            config_name = config_name + str(position) + ".yaml"
            log_name = "logs/log_" + str(position) + ".txt"
    return dev_name, config_name, log_name

#Initial delay is necessary to let prometheus collect some data before trying to sync with it.
print(f"Starting... initial delay of {initial_delay}\n")
pause.sleep(initial_delay)


on_start()
start_time = sync_clock()
next_iteration = start_time + time_sleep_sec
starting_val = get_starting_values()
history_file = open("dev_num_log.txt", "w")

mean_conn_dev = starting_val.to_numpy()
max_val = mean_conn_dev.max()

while 1:
    if debug:
        print("Starting iteration " + str(iteration) + " | mean index: " + str(i))

    mean = mean_conn_dev[i]
    stand_dev = (2 / max_val) * mean
    data = random.normal(loc=mean, scale=stand_dev, size=1)

    num_dev = round(data[0])

    if debug:
        print("Number Actual simul datedevicesof dev: " + str(num_dev))
    history_file.write("pos:" + str(i) + " " + str(num_dev) + "\n")
    history_file.flush()

    if num_dev < 0:
        num_dev = 0

    if i < (len(mean_conn_dev) - 1):
        i = i + 1
    else:
        i = 0

    diff = connected_devices_num - num_dev
    print(f"[{datetime.now()}] [INFO] Simulated devices will be: {num_dev} | Difference: {-diff}")
    if debug:
        print(f"[{time.time()}] [INFO] Simulated devices will be: {num_dev} | Difference: {-diff}")
    sys.stdout.flush()

    if diff < 0:
        connected_devices_num = add_device(connected_devices_num, abs(diff))
    elif diff > 0:
        connected_devices_num = remove_device(connected_devices_num, diff)

    iteration = iteration + 1

    print(f"[{datetime.now()}] [INFO] Actual simulated devices are now: {connected_devices_num} | Difference: {-diff}")
    if debug:
        print(f"[{time.time()}] [INFO] Actual simulated devices are now: {connected_devices_num} | Difference: {-diff}")
    sys.stdout.flush()

    if debug:
        print(str(time_sleep_sec) + "s to next iter")

    pause.until(next_iteration)
    next_iteration = next_iteration + time_sleep_sec
    sys.stdout.flush()
