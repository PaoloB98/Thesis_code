#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 28 10:26:11 2022

@author: paolo
"""

import os
import signal
from subprocess import Popen
from numpy import random
from typing import List
import time
import pandas as pd
from datetime import datetime


class Device:
    pid: int = -1
    dev_imsi: str = "imsi-2089300000000"

    def __init__(self, pid, dev_imsi):
        self.pid = pid
        self.dev_imsi = dev_imsi


# Configuration
time_sleep_sec = 1

connected_devices: List[Device] = []
connected_devices_num = 0
mean_conn_dev = [4, 2, 3, 2, 3, 2, 3, 5, 2, 7, 8, 9, 9, 10, 12, 10, 10, 11, 11, 12, 12, 12, 8, 5]
i = 0
iteration = 1
history_file = None
starting_val: pd.Series


def on_close(sig, frame):
    remove_device(connected_devices_num, connected_devices_num, connected_devices)
    print("Closing...\n")
    history_file.close()
    exit(0)


def add_device(actual_dev: int, num_to_add, lista: List[Device]):
    for iter in range(0, num_to_add):
        dev_name = "imsi-2089300000000"
        log_name = "log"
        config_name = "config/free5gc-ue"
        position = actual_dev + iter

        if position < 10:
            dev_name = dev_name + str(0) + str(position)
            config_name = config_name + str(0) + str(position) + ".yaml"
            log_name = "logs/log_0" + str(position) + ".txt"
        else:
            dev_name = dev_name + str(position)
            config_name = config_name + str(position) + ".yaml"
            log_name = "logs/log_" + str(position) + ".txt"

        dev_std_out = open(log_name, 'a+')
        # Popen(["/home/paolo/code/UERANSIM/build/nr-ue", "-c", config_name])
        proc_id = Popen(["/home/paolo/code/UERANSIM/build/nr-ue", "-c", config_name], stdout=dev_std_out,
                        stderr=dev_std_out, shell=False).pid
        # print("/home/paolo/code/UERANSIM/build/nr-ue" + " -c " + config_name + "\n")
        # subprocess.DEVNULL
        new_dev: Device = Device(pid=proc_id, dev_imsi=dev_name)
        lista.append(new_dev)
    return actual_dev + num_to_add


def remove_device(actual_dev: int, num_to_rem, lista: List[Device]):
    for i in range(0, num_to_rem):
        position = actual_dev - 1 - i

        device = lista[position]

        Popen(["/home/paolo/code/UERANSIM/build/nr-cli", device.dev_imsi, "-e", "deregister switch-off"])
        # print("/home/paolo/code/UERANSIM/build/nr-cli" + dev_name + " -e 'deregister switch-off'\n")
        time.sleep(0.05)
        os.kill(device.pid, signal.SIGTERM)
        lista.pop()
        assert (position >= 0)
    return actual_dev - num_to_rem


def parser(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


def get_starting_values():
    starting_values = pd.read_csv('starting_data.csv', usecols=['time', 'num_usr'], parse_dates=[0], index_col=0,
                                  date_parser=parser)

    return starting_values


def initial_setup():
    signal.signal(signal.SIGTERM, on_close)
    signal.signal(signal.SIGINT, on_close)
    signal.signal(signal.SIGHUP, on_close)

    if os.path.exists("./logs"):
        if not(os.path.isdir("./logs")):
            os.remove("./logs")
            os.mkdir("./logs")
    else:
        os.mkdir("./logs")


print("Starting...\n")
initial_setup()
starting_val = get_starting_values()
history_file = open("dev_num_log.txt", "a+")

mean_conn_dev = starting_val.to_numpy()
max_val = mean_conn_dev.max()

j: int = 0
while 1:
    print("Starting iteration " + str(iteration) + " | mean index: " + str(i))

    mean = mean_conn_dev[i]
    stand_dev = (2 / max_val) * mean
    data = random.normal(loc=mean, scale=stand_dev, size=1)

    num_dev = round(data[0])

    print("Number of dev: " + str(num_dev))
    history_file.write("pos:" + str(i) + " " + str(num_dev) + "\n")
    history_file.flush()

    if num_dev < 0:
        num_dev = 0

    if ((iteration % 4) == 0) & (iteration > 0):
        if i < (len(mean_conn_dev) - 1):
            i = i + 1
        else:
            i = 0

    diff = len(connected_devices) - num_dev

    if diff < 0:
        print(str(abs(diff)) + " devices will be added")
        connected_devices_num = add_device(connected_devices_num, abs(diff), connected_devices)
    elif diff > 0:
        print(str(diff) + " devices will be removed")
        connected_devices_num = remove_device(connected_devices_num, diff, connected_devices)

    print("Iteration done\n")

    iteration = iteration + 1

    j = j + 1
    print(str(time_sleep_sec) + "s to next iter")
    time.sleep(time_sleep_sec)
