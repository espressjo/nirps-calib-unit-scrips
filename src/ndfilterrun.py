#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 18:51:48 2022

@author: noboru
"""
from ndfilterlog import cfgfile,nd_filter_log
import numpy as np
from sys import argv
from nirps_plc_ndfiltre import beckoff
from pm100 import pm100
class argument:
    def __init__(self):
        self.items = {}
        for arg in argv:
            if '=' in arg:
                self.items[arg.split('=')[0]] = arg.split('=')[1]
            else:
                self.items[arg] = 'Null'
    def __contains__(self, item):
        return item in self.items
    def __getitem__(self, item):
        if item in self.items:
            return self.items[item]
        else:
            None
class ndfilter:
    """
    main methods are get_data, log, move_selector and run
    """
    def __init__(self):
        self.conf = cfgfile()

        
        self.log = nd_filter_log()
        #default position list
        self.beckoff_ip = self.conf['beckoff-ip']
        #self.list_position1 = np.arange(92640,93001,40)
        #self.list_position2 = np.arange(92605,92966,40)
        args = argument()
        self.pm100_simul = '--pm100-simul' in args
        self.beckoff_simul = '--plc-simul' in args
        if '--selector1' in args:
            self.selector = 1
        elif '--selector2' in args:
            self.selector = 2
        else:
            print("You must specify a selector to perform the test with.")
            exit(0)
        if all(['--start-position' in args, '--stop-position' in args]):
            start = int(args['--start-position'])
            stop = int(args['--stop-position'])
        else:
            print("Please specify selector positions.")
            exit(0)
        if '--selector-increment' in args:
            inc = int(args['--selector-increment'])
        else:
            inc = self.conf['selector-inc']
            self.position = np.arange(start,stop,inc)

        if '--beckoff-ip' in args:
            self.beckoff_ip = args['--beckoff-ip']
        if '--pm100' in args:
            self.get_data = self.get_flux_pm100
            if self.selector==1:
                self.log_data = self.log.log_selector_1_flux
            else:
                self.log_data = self.log.log_selector_2_flux
        elif '--det' in args:
            self.get_data = self.get_img_det
            if self.selector==1:
                self.log_data = self.log.log_selector_1_det
            else:
                self.log_data = self.log.log_selector_2_det
        else:
            print("Please specify which device you want to run the test with;\n\t--pm100 (power meter)\n\t--det (H4RG detector)")
            exit(0)
        
    def get_img_det(self):
        print("Not yet implemented")
    
    def get_flux_pm100(self):
        
        with pm100(simulation=self.pm100_simul) as pm:
            return pm.measure()
    def move_selector(self,position):
        with beckoff(self.beckoff_ip,hwsimul=self.beckoff_simul) as boff:
            return boff.set_NDFilter(self.selector, self.position)
        
    def run(self):
        for p in self.position:
            self.move_selector(p)
            data = self.get_data()
            self.log_data(p,data)
def help():
    print("\n\t:::: ND Filter Test Helper ::::\n")
    print("\t--selector1: perform test with selector 1")
    print("\t--selector2: perform test with selector 2")
    print("\t--start-position: start position of chosen selector")
    print("\t--stop-position: stop position of chosen selector")
    print("\t--selector-increment: increment of selector") 
    print("\t--plc-simul: use PLC in simulation mode")
    print("\t--beckoff-ip: Define IP adresse for beckoff (PLC)")
    print("\t--pm100: Perform test using power meter")
    print("\t--pm100-simul: Use the powermeter in simulation mode")
    print("\t--det: Perform test using infrared detector")
if '__main__' in __name__:
    
    if '--help' in argv:
        help()
        exit(0)
    ND = ndfilter()
    ND.run()