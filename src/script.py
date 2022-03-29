#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 15:41:13 2022

@author: noboru
"""

from nirps_plc_ndfiltre import beckoff,argument

from numpy import linspace
from os.path import join
from datetime import datetime
from ndfilterlog import cfgfile
from arguments import argument
from sys import argv
args = argument()

cfg = cfgfile()
fmt = "%Y%m%d%H%M%S"
#steps = 100 
simul = False
ip = cfg['beckoff-ip']#fetch the ip of the beckoff
port = cfg['beckoff-port']

if '__main__' in __name__:
    with beckoff(ip=ip) as beck:
        
        beck.set_selector(2,90)
        print("Starting scan")
        beck.set_selector_velocity(2,0.5)
        beck.set_selector(2,120)
        