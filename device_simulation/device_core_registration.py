import requests
import json

f = open('data/device_reg_body.json')
data = json.load(f)
device_number = 1000

for i in range(0, 1000):
    print("Iteration " + str(i) + "\n")
    num_str = ""
    if (i < 10):
        num_str = str(0) + str(i)
    else:
        num_str = str(i)

    imsi = "imsi-2089300000000" + num_str
    url = f"http://localhost:5000/api/subscriber/{imsi}/20893"
    data['ueId'] = imsi
    headers_c = {"Content-Type": "application/json", "Accept-Charset": "utf-8", "Token": "admin"}

    response = requests.post(url,json=data,headers=headers_c)

    if(response.status_code==201):
        print(f"Successfully added device {imsi}")
    else:
        print(f"Error while adding {imsi}")
