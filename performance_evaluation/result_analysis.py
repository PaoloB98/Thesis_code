import pandas as pd

nwdaf = False

if nwdaf:
    filename = "results_on.csv"
    monitoring_results = pd.read_csv("results/nwdaf_on/container_cpu_system_seconds_total.csv")
else:
    filename = "results_off.csv"
    monitoring_results = pd.read_csv("results/nwdaf_off/container_cpu_system_seconds_total.csv")


final_data = pd.DataFrame(columns={"container", "metric_name", "mean", "variance"})

nf_list = monitoring_results["container"].unique()

tmp_list = []
for container in nf_list:
    nf_perf_list = monitoring_results["container"] == container
    name = monitoring_results[nf_perf_list]["metric_name"].iat[0]
    mean = monitoring_results[nf_perf_list]["value"].mean()
    variance = monitoring_results[nf_perf_list]["value"].var()
    tmp_list.append({"container": container, "metric_name": name, "mean": mean, "variance": variance})

final_data = final_data.from_records(tmp_list)

csv_to_save = final_data.to_csv()
file = open(filename, "w+")
file.write(csv_to_save)
file.flush()
file.close()

exit(0)
