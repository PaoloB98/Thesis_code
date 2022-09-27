import time

import pandas as pd
import pause
import requests
import os
import subprocess

nwdaf_on = 1
minutes_to_test: int = 60
starting_dir = os.getcwd()
address = "localhost:9089"
protocol = "http://"
scraping_API = protocol + address + "/api/v1/query?query="
metrics_to_ask = ["container_cpu_system_seconds_total", "container_memory_usage_bytes"]
working_dir = "/home/paolo/Coding/free5gc-compose-thesis"
column_names = ["start_time", "end_time", "metric_name", "value", "container", "average", "min_average"]


def get_metric(dataframe, metric_name, start_time, end_time, average: bool, minutes_of_average):
    if average:
        url = f"{scraping_API}avg_over_time({metric_name}[{minutes_of_average}m])"
    else:
        url = f"{scraping_API}{metric_name}@{end_time}-{metric_name}@{start_time}"

    response = requests.get(url)
    rsp_json = response.json()
    if dataframe is None:
        dataframe = pd.DataFrame(columns=column_names)

    tmp_df = pd.DataFrame(columns=column_names)
    tmp_list = []
    for element in rsp_json['data']['result']:
        if "name" in element['metric']:
            container_name = element['metric']['name']
        else:
            continue
        time_of_metric = element['value'][0]
        metric_value = element['value'][1]
        tmp_list.append(
            {"start_time": start_time, "end_time": end_time, "metric_name": metric_name, "value": metric_value,
             "container": container_name, "average": average, "minutes_average": minutes_of_average})
    df_to_append = tmp_df.from_records(tmp_list)
    dataframe = pd.concat([dataframe, df_to_append])
    return dataframe


def save_df_to_csv(dataframe: pd.DataFrame, metric_name):
    if nwdaf_on:
        filename = f"./results/nwdaf_on/{metric_name}.csv"
    else:
        filename = f"./results/nwdaf_off/{metric_name}.csv"
    file = open(filename, "w+")
    csv_form = dataframe.to_csv()
    file.write(csv_form)
    file.close()


def setup():
    os.chdir(starting_dir)
    if os.path.exists("./results"):
        if not (os.path.isdir("./results")):
            os.remove("./results")
            os.mkdir("./results")
    else:
        os.mkdir("./results")

    if os.path.exists("./results/nwdaf_on"):
        if not (os.path.isdir("./results/nwdaf_on")):
            os.remove("./results/nwdaf_on")
            os.mkdir("./results/nwdaf_on")
    else:
        os.mkdir("./results/nwdaf_on")

    if os.path.exists("./results/nwdaf_off"):
        if not (os.path.isdir("./results/nwdaf_off")):
            os.remove("./results/nwdaf_off")
            os.mkdir("./results/nwdaf_off")
    else:
        os.mkdir("./results/nwdaf_off")


def load_data_from_csv(metric_name):
    if nwdaf_on:
        filename = f"./results/nwdaf_on/{metric_name}.csv"
    else:
        filename = f"./results/nwdaf_off/{metric_name}.csv"
    if os.path.isfile(filename):
        file = open(filename, "r+")
        content = pd.read_csv(file)
        file.close()
        return content
    else:
        return None


setup()
start_time = time.time()
wait_til = start_time

old_data_1 = load_data_from_csv(metrics_to_ask[0])
old_data_2 = load_data_from_csv(metrics_to_ask[1])
os.chdir(working_dir)
if nwdaf_on:
    proc_id = subprocess.Popen(["docker", "compose", "up", "-d"], stdout=subprocess.DEVNULL, shell=False).pid
else:
    proc_id = subprocess.Popen(["docker", "compose", "up", "-d", "redis", "db", "free5gc-upf", "free5gc-nrf",
                                "prometheus", "ueransim", "free5gc-n3iwf", "free5gc-ausf", "free5gc-amf", "free5gc-udr",
                                "free5gc-pcf", "free5gc-udm", "free5gc-nssf", "free5gc-smf", "free5gc-nrf",
                                "free5gc-webui", "cadvisor"], stdout=subprocess.DEVNULL, shell=False, ).pid
os.chdir(starting_dir)

for i in range(1, minutes_to_test):
    wait_til = wait_til + 60
    pause.until(wait_til)
    print(f"{minutes_to_test - i} minutes to TEST END")

df1 = get_metric(dataframe=old_data_1, metric_name=metrics_to_ask[0], start_time=start_time, end_time=wait_til,
                 average=False, minutes_of_average=0)
df2 = get_metric(dataframe=old_data_2, metric_name=metrics_to_ask[1], start_time=start_time, end_time=wait_til,
                 average=True, minutes_of_average=minutes_to_test)

save_df_to_csv(df1, metrics_to_ask[0])
save_df_to_csv(df2, metrics_to_ask[1])
