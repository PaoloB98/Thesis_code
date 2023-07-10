import time

import pandas as pd
import pause
import requests
import os
import subprocess
import sys

deploy = True
nwdaf_on = 1
minutes_to_test: int = 60
starting_dir = os.getcwd()
address = "localhost"
arguments = sys.argv[1:]
if len(arguments) > 1:
    if arguments[0] == "-addr":
        address = arguments[1]

protocol = "http://"
scraping_API = protocol + address + ":9089/api/v1/query?query="
metrics_to_ask = ["container_cpu_system_seconds_total", "container_memory_usage_bytes",
                  "scaph_process_power_consumption_microwatts"]
working_dir = "/home/ubuntu/free5gc-compose"
column_names = ["start_time", "end_time", "metric_name", "value", "container", "average", "min_average"]
exe_names = ["amf", "ausf", "nwdaf", "n3iwf", "nr-gnb", "nrf", "nssf", "pcf", "smf", "udm", "udr", "webui", "nr-ue",
             "prometheus", "cadvisor", "scaphandre", "grafana", "python3", "redis-server"]


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
    dataframe = pd.concat([dataframe, df_to_append], ignore_index=True)
    return dataframe


def get_metric_sum_over_time(dataframe, metric_name, end_time, exe_name, minutes_of_sum: int):
    """
    Gets the sum over time of a metric. The sum is taken from the end_time back to the starting time (defined by the
    range of the sum, given by minutes_of_sum value)
    """
    metric_name_filtered = metric_name+"{container_scheduler='docker',exe='" + exe_name + "'}"
    url = f"{scraping_API}sum(sum_over_time({metric_name_filtered}[{minutes_of_sum}m] @ {end_time}))"

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
            container_name = f"{exe_name}_{metric_name}"
        time_of_metric = element['value'][0]
        metric_value = element['value'][1]
        tmp_list.append(
            {"end_time": end_time, "metric_name": metric_name, "value": metric_value,
             "container": container_name, "minutes_of_sum": minutes_of_sum})
    df_to_append = tmp_df.from_records(tmp_list)
    dataframe = pd.concat([dataframe, df_to_append], ignore_index=True)
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
        content = pd.read_csv(file, index_col=[0])
        file.close()
        return content
    else:
        return None


setup()

#  We give one extra minute to services for starting. In particular to cAdvisor to start metering.
start_test_time = time.time() + 60
wait_til = start_test_time

existing_data_cpu_tot_sec = load_data_from_csv(metrics_to_ask[0])
existing_data_mem_usage = load_data_from_csv(metrics_to_ask[1])
existing_data_power_usage = load_data_from_csv(metrics_to_ask[2])
os.chdir(working_dir)

if not deploy:
    print("Starting containers...")
    if nwdaf_on:
        proc_id = subprocess.Popen(["docker", "compose", "up", "-d"], stdout=subprocess.DEVNULL).pid
    else:
        proc_id = subprocess.Popen(["docker", "compose", "up", "-d", "redis", "db", "free5gc-upf", "free5gc-nrf",
                                    "prometheus", "ueransim", "free5gc-n3iwf", "free5gc-ausf", "free5gc-amf", "free5gc-udr",
                                    "free5gc-pcf", "free5gc-udm", "free5gc-nssf", "free5gc-smf", "free5gc-nrf",
                                    "free5gc-webui", "cadvisor"], stdout=subprocess.DEVNULL, shell=False, ).pid
else:
    print("Working in deploy mode. Containers will be not started. Just measuring the performance.")
os.chdir(starting_dir)

for i in range(0, minutes_to_test):
    wait_til = wait_til + 60
    pause.until(wait_til)
    print(f"{minutes_to_test - i - 1} minutes to TEST END")

df1 = get_metric(dataframe=existing_data_cpu_tot_sec, metric_name=metrics_to_ask[0], start_time=start_test_time, end_time=wait_til,
                 average=False, minutes_of_average=0)
df2 = get_metric(dataframe=existing_data_mem_usage, metric_name=metrics_to_ask[1], start_time=start_test_time, end_time=wait_til,
                 average=True, minutes_of_average=minutes_to_test)

#  For each container we get the consumption and add it to the existing data frame
df3 = existing_data_power_usage
for exe in exe_names:
    df3 = get_metric_sum_over_time(dataframe=df3, metric_name=metrics_to_ask[2], end_time=wait_til, exe_name=exe,
                                   minutes_of_sum=minutes_to_test)

save_df_to_csv(df1, metrics_to_ask[0])
save_df_to_csv(df2, metrics_to_ask[1])
save_df_to_csv(df3, metrics_to_ask[2])
