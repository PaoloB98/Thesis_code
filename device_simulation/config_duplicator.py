#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 17:57:29 2022

@author: paolo
"""

import os
import re
import sys

device_number = 1000
print(os.getcwd())
imeis = 356938035643803
source_file = "free5gc-ue.yaml"
arguments = sys.argv[1:]
if len(arguments) > 0:
    if arguments[0] == "-d":
        source_file = "free5gc-ue-deploy.yaml"

if os.path.exists("./config"):
    if not(os.path.isdir("./config")):
        os.remove("./config")
        os.mkdir("./config")
else:
    os.mkdir("./config")

for i in range(0,device_number):
    print("Iteration " + str(i)+ "\n")
    num_str = ""
    if(i<10):
         num_str = "00"+str(i)
    else:
        if(i<=99):
            num_str = "0"+str(i)
        else:
            num_str = str(i)
    
    filename = "config/free5gc-ue" + num_str + ".yaml"
    imsi = "imsi-208930000000" + num_str
    imeis= imeis+1
    imeifinal = f"imei: '{imeis}'"
    
    #shutil.copyfile("free5gc-ue.yaml", filename)
    
    fin = open(source_file, "r")
    fout = open(filename, "w")
    
    for line in fin:
        stri = line.replace('imsi-208930000000003', imsi)
        stri = re.sub("imei: '[0-9]*'", imeifinal, stri)
        fout.write(stri)
    
    fout.close()
    fin.close()
        

                   