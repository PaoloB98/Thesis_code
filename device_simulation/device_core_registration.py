import requests
import json
import sys

f = open('data/device_reg_body.json')
data = json.load(f)
device_number = 1000

address = "localhost"
arguments = sys.argv[1:]
if len(arguments) > 1:
    if arguments[0] == "-addr":
        address = arguments[1]

for i in range(0, device_number):
    print("Iteration " + str(i) + "\n")
    num_str = ""
    if (i < 10):
        num_str = "00" + str(i)
    else:
        if i <= 99:
            num_str = "0" + str(i)
        else:
            num_str = str(i)

    imsi = "imsi-208930000000" + num_str
    url = f"http://{address}:5000/api/subscriber/{imsi}/20893"
    data['ueId'] = imsi
    headers_c = {"Content-Type": "application/json", "Accept-Charset": "utf-8", "Token": "admin"}

    response = requests.post(url, json=data, headers=headers_c)

    if(response.status_code==201):
        print(f"Successfully added device {imsi}")
    else:
        print(f"Error while adding {imsi}")
        print(response)

