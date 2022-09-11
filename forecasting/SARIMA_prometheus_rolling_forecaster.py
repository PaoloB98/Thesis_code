import signal
import time
import requests
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.statespace.sarimax import SARIMAXResults
from datetime import datetime
import datetime as dt

scraping_interval: int = 10
scraping_API: int = "http://localhost:9090/api/v1/query?query=free5gc_core_connected_3gpp_ues"
samples = pd.Series()
my_order = (1, 1, 1)
seasonal_period = 24
my_seasonal_order = (1, 1, 1, seasonal_period)
pred_log_file = None

def on_close(sig, frame):
    print("Closing...\n")
    pred_log_file.close()
    exit(0)

def round_seconds(obj: dt.datetime) -> dt.datetime:
    if obj.microsecond >= 500_000:
        obj += dt.timedelta(seconds=1)
    return obj.replace(microsecond=0)

def collect_data():
    print("Collecting data...\n")
    response = requests.get(scraping_API)
    rsp_json = response.json()
    time_sec = rsp_json['data']['result'][0]['value'][0]
    value = rsp_json['data']['result'][0]['value'][1]
    metric_name = rsp_json['data']['result'][0]['metric']['__name__']

    datetime_time = round_seconds(datetime.fromtimestamp(time_sec))


    tmp_serie = pd.Series([value], index=[datetime_time])
    new_samples = pd.concat([samples, tmp_serie])
    new_samples = new_samples.astype(int)

    return new_samples

#Imposta il metodo di chiusura.
signal.signal(signal.SIGTERM, on_close)
signal.signal(signal.SIGINT, on_close)
#Il numero minimo di campioni per far partire la previsione
min_num_sample = seasonal_period*2
while samples.size<min_num_sample:
    samples = collect_data()

    print("Current samples: "+str(samples.size)+"\n")
    time.sleep(scraping_interval)

pred_log_file = open("pred.log", "a+")
i: int = min_num_sample
minimum = 0
maximum = 0
comulative_sqr_err : float = 0
prediction_mean = 0
while i > 0:
    samples = collect_data()
    #When it's not the first iteration it computes mse of with respect to predictions
    if(i>min_num_sample):
        comulative_sqr_err = comulative_sqr_err + (prediction_mean.iloc[0]-samples.iloc[-1]) ** 2
        mse = comulative_sqr_err/(i-min_num_sample)
        print("Mean square error: " + str(mse) + "\n")

    samples = samples.asfreq("10S")

    # define data freq: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    model = SARIMAX(samples, order=my_order, seasonal_order=my_seasonal_order)

    fitted_model : SARIMAXResults = model.fit()

    forecast = fitted_model.get_forecast(1)
    prediction_mean = forecast.predicted_mean

    conf_int = forecast.conf_int(alpha=0.05)

    minimum = conf_int.iloc[0].at["lower y"]
    maximum = conf_int.iloc[0].at["upper y"]

    pred_log_file.write("["+str(minimum)+" "+str(maximum)+"]\n")

    print("\n")
    print(conf_int)
    print("\n")

    i = i + 1
    time.sleep(scraping_interval)











