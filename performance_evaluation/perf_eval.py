import time
import pause
import requests
import os
import signal
import subprocess

minutes_to_test: int = 60
address = "localhost:9090"
protocol = "http://"
scraping_API = protocol + address + "/api/v1/query?query=process_cpu_seconds_total"
working_dir = "/home/paolo/Coding/free5gc-compose-thesis"

response = requests.get(scraping_API)
rsp_json = response.json()
time_sec_start = rsp_json['data']['result'][1]['value'][0]
value_start = rsp_json['data']['result'][1]['value'][1]
metric_name = rsp_json['data']['result'][1]['metric']['__name__']
print(f"CPU time start: {value_start} | starting time: {time_sec_start}")

start_time = time.time()
wait_til = start_time
os.chdir(working_dir)
proc_id = subprocess.Popen(["docker", "compose", "up"], stdout=subprocess.DEVNULL, shell=False).pid

for i in range(1, minutes_to_test):
    wait_til = wait_til + 60
    pause.until(wait_til)
    print(f"{60 - i} minutes to TEST END")

os.kill(proc_id, signal.SIGTERM)

response = requests.get(scraping_API)
rsp_json = response.json()
time_sec_end = rsp_json['data']['result'][1]['value'][0]
value_end = rsp_json['data']['result'][1]['value'][1]

print(f"CPU time start: {value_end} | starting time: {time_sec_end}")
total_sec = 60*minutes_to_test
total_time = float(value_end)-float(value_start)
print(f"CPU time used: {total_time} seconds of {total_sec}")
