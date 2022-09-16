#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 28 10:56:12 2022

@author: Paolo Bono
"""

import signal
import time
import requests
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.statespace.sarimax import SARIMAXResults
from datetime import datetime
import sys
import pause

scraping_interval_sec: int = 10
seasonal_period = 24
max_samples_for_training = seasonal_period * 14
# Minimum number of samples to start predicting
min_num_sample = seasonal_period * 3
next_sample_collection = 0

address = "localhost:9090"
arguments = sys.argv[1:]
if len(arguments) > 1:
    if arguments[0] == "-addr":
        address = arguments[1]

protocol = "http://"
scraping_API = protocol + address + "/api/v1/query?query=free5gc_core_connected_3gpp_ues"
scraping_API_range = protocol + address + "/api/v1/query_range?query=free5gc_core_connected_3gpp_ues"
custom_headers = {'User-Agent': 'python-requests/2.28.1', 'Accept': '*/*'}

samples = pd.Series()
my_order = (1, 1, 1)
my_seasonal_order = (1, 1, 1, seasonal_period)
pred_log_file = None


def test_connection():
    response = requests.get(scraping_API)


def on_close(sig, frame):
    print("Closing...\n")
    if pred_log_file is not None:
        pred_log_file.close()
    exit(0)


def collect_initial_data():
    actual_time = time.time()
    end_time = actual_time - (actual_time % scraping_interval_sec)
    start_time = end_time - (scraping_interval_sec * min_num_sample)
    next_collection = end_time + scraping_interval_sec
    uri = f"{scraping_API_range}&start={start_time}&end={end_time}&step={scraping_interval_sec}s"
    # custom_params = {'start':str(start_time),'end':str(end_time),'step':str(scraping_interval_sec)+'s'}
    response = requests.get(uri, headers=custom_headers)

    rsp_json = response.json()
    list_rsp = rsp_json['data']['result'][0]['values']
    time_sec_list = [(el[0] - (el[0] % scraping_interval_sec)) for el in list_rsp]
    values = [el[1] for el in list_rsp]

    # Exclude all starting zeros
    index_for_valid_data = 0
    for i in range(0, len(values)):
        if values[i] != '0':
            break
        index_for_valid_data = index_for_valid_data + 1

    time_sec_list = time_sec_list[index_for_valid_data:]
    values = values[index_for_valid_data:]

    datetime_time = []
    for ts in time_sec_list:
        datetime_time.append(datetime.fromtimestamp(ts))

    new_samples = pd.Series(values, index=datetime_time)
    new_samples = new_samples.astype(int)

    if new_samples.size > min_num_sample:
        # Removes older sample
        new_samples = new_samples.drop(new_samples.index[0])

    return new_samples, next_collection


def collect_data():
    response = requests.get(f"{scraping_API}&time={next_sample_collection}")
    rsp_json = response.json()
    time_sec = rsp_json['data']['result'][0]['value'][0]
    value = rsp_json['data']['result'][0]['value'][1]
    metric_name = rsp_json['data']['result'][0]['metric']['__name__']

    time_sec = time_sec - (time_sec % scraping_interval_sec)
    datetime_time = datetime.fromtimestamp(time_sec)

    tmp_serie = pd.Series([value], index=[datetime_time])
    new_samples = pd.concat([samples, tmp_serie])
    if new_samples.size > max_samples_for_training:
        # Removes older sample
        new_samples = new_samples.drop(new_samples.index[0])

    new_samples = new_samples.astype(int)

    print("New sample has been collected: " + str(datetime_time) + " | " + str(value))
    print("Total samples: " + str(new_samples.size))
    sys.stdout.flush()

    return new_samples, next_sample_collection + scraping_interval_sec


# Imposta il metodo di chiusura
signal.signal(signal.SIGTERM, on_close)
signal.signal(signal.SIGINT, on_close)
samples, next_sample_collection = collect_initial_data()  # Get samples from prometheus
print("Initial samples: " + str(samples.size))

# If there wasn't enough valid samples, wait for filling
while samples.size < min_num_sample:
    pause.until(next_sample_collection)
    samples, next_sample_collection = collect_data()
    # print("Current samples: "+str(samples.size)+"\n")

samples_freq = samples.asfreq('S')
pred_log_file = open("pred.log", "a+")
i: int = min_num_sample
minimum = 0
maximum = 0
comulative_sqr_err: float = 0
prediction_mean = 0

while i > 0:
    # define model
    model = SARIMAX(samples, order=my_order, seasonal_order=my_seasonal_order)

    fitted_model: SARIMAXResults = model.fit()

    forecast = fitted_model.get_forecast(seasonal_period)
    prediction_mean = forecast.predicted_mean
    conf_ints = forecast.conf_int()

    for j in range(0, seasonal_period):
        i = i + 1
        pause.until(next_sample_collection)
        samples, next_sample_collection = collect_data()
        minimum = conf_ints.iloc[j].at["lower y"]
        maximum = conf_ints.iloc[j].at["upper y"]
        pred_log_file.write("[" + str(minimum) + " " + str(maximum) + "]\n")

        observation = samples.iloc[-1]  # Prendo l'ultimo osservato
        print("Prediction: " + str(prediction_mean.iloc[j]) + " --> Actual value: " + str(observation))
        comulative_sqr_err = comulative_sqr_err + (prediction_mean.iloc[j] - observation) ** 2
        mse = comulative_sqr_err / (i - min_num_sample)
        print("Mean square error: " + str(mse) + "\n")
        sys.stdout.flush()
