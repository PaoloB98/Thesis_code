import signal
import time
import requests
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.statespace.sarimax import SARIMAXResults
from datetime import datetime
import pause

scraping_interval_sec: int = 1
seasonal_period = 24
max_samples_for_training = seasonal_period*14
#Minimum number of samples to start predicting
min_num_sample = seasonal_period*2

scraping_API = "http://localhost:9090/api/v1/query?query=free5gc_core_connected_3gpp_ues"
scraping_API_range = "http://localhost:9090/api/v1/query_range?query=free5gc_core_connected_3gpp_ues"
custom_headers = {'User-Agent': 'python-requests/2.28.1', 'Accept': '*/*'}

samples = pd.Series()
my_order = (1, 1, 1)

my_seasonal_order = (1, 1, 1, seasonal_period)
pred_log_file = None

def on_close(sig, frame):
    print("Closing...\n")
    pred_log_file.close()
    exit(0)

def collect_initial_data():
    end_time = time.time()
    start_time = end_time - (scraping_interval_sec*min_num_sample)
    uri = f"{scraping_API_range}&start={start_time}&end={end_time}&step={scraping_interval_sec}s"
    #custom_params = {'start':str(start_time),'end':str(end_time),'step':str(scraping_interval_sec)+'s'}
    response = requests.get(uri, headers=custom_headers)

    rsp_json = response.json()
    list_rsp = rsp_json['data']['result'][0]['values']
    time_sec_list = [(el[0]-(el[0] % scraping_interval_sec)) for el in list_rsp]
    values = [el[1] for el in list_rsp]

    #Exclude all starting zeros
    index_for_valid_data = 0
    for i in range(0, len(values)):
        if values[i] != '0':
            break
        index_for_valid_data = index_for_valid_data+1

    time_sec_list = time_sec_list[index_for_valid_data:]
    values = values[index_for_valid_data:]

    datetime_time = []
    for ts in time_sec_list:
        datetime_time.append(datetime.fromtimestamp(ts))

    new_samples = pd.Series(values, index=datetime_time)
    new_samples = new_samples.astype(int)

    return new_samples


def collect_data():
    response = requests.get(scraping_API)
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

    return new_samples


# Imposta il metodo di chiusura
signal.signal(signal.SIGTERM, on_close)
signal.signal(signal.SIGINT, on_close)
samples = collect_initial_data() #Get samples from prometheus

#If there wasn't enough valid samples, wait for filling
while samples.size<min_num_sample:
    samples = collect_data()
    print("Current samples: "+str(samples.size)+"\n")
    time.sleep(scraping_interval_sec)

samples_freq = samples.asfreq('S')
pred_log_file = open("pred.log", "a+")
i: int = min_num_sample
minimum = 0
maximum = 0
comulative_sqr_err : float = 0
prediction_mean = 0

while i > 0:
    # define model
    model = SARIMAX(samples, order=my_order, seasonal_order=my_seasonal_order)

    fitted_model : SARIMAXResults = model.fit()

    forecast = fitted_model.get_forecast(seasonal_period)
    prediction_mean = forecast.predicted_mean
    conf_ints = forecast.conf_int()


    for j in range(0,seasonal_period):
        i = i + 1
        collect_data()
        minimum = conf_ints.iloc[j].at["lower y"]
        maximum = conf_ints.iloc[j].at["upper y"]
        pred_log_file.write("[" + str(minimum) + " " + str(maximum) + "]")

        observation = samples.iloc[-1] #Prendo l'ultimo osservato
        print("Prediction: " + str(prediction_mean.iloc[0]) + " --> Actual value: " + str(observation))
        comulative_sqr_err = comulative_sqr_err + (prediction_mean.iloc[0] - observation) ** 2
        mse = comulative_sqr_err / (i - min_num_sample)
        print("Mean square error: " + str(mse) + "\n")

        time.sleep(scraping_interval_sec)


#Mettere un limite ai sample che possono essere raccolti, buttando via i vecchi!








