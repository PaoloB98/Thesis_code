#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 17:57:29 2022

@author: paolo
"""

import os
import re

print(os.getcwd())
imeis = 356938035643803

for i in range(0,99):
    print("Iteration " + str(i)+ "\n")
    num_str = ""
    if(i<10):
         num_str = str(0)+str(i)
    else:
         num_str = str(i)
    
    filename = "config/free5gc-ue" + num_str + ".yaml"
    imsi = "imsi-2089300000000" + num_str
    imeis= imeis+1
    imeifinal = f"imei: '{imeis}'"
    
    #shutil.copyfile("free5gc-ue.yaml", filename)
    
    fin = open("free5gc-ue.yaml", "r")
    fout = open(filename, "w")
    
    for line in fin:
        stri = line.replace('imsi-208930000000003', imsi)
        stri = re.sub("imei: '[0-9]*'", imeifinal, stri)
        fout.write(stri)
    
    fout.close()
    fin.close()
        

                   