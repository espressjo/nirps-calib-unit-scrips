#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 13:23:38 2022

@author: noboru
"""

import platform    
import subprocess  
from sys import argv
from colorama import init
init()
from colorama import Fore,Style

ips_ccr = {"PLC":"134.171.102.126",
       "Opto-22":"134.171.102.127",
       "iBoot1":"134.171.102.128",
       "iBoot2":"134.171.102.129",
       "iBoot3":"134.171.102.130",
       "Lakeshore224-1":"134.171.102.131",
       "Lakeshore224-2":"134.171.102.132",
       "IOLAN":"134.171.102.133",
       "Cryocooler1":"134.171.102.134",
       "Cryocooler2":"134.171.102.135",
       "BE-CCR temperature ctrl":"134.171.102.136",
       "DCC":"134.171.102.137"}
ips_calib = {"PLC":"134.171.102.122",
       "FP vac. gauge":"134.171.102.139",
       "Lakeshore 336":"134.171.102.138"}

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
    def __str__(self):
        l = ["%s: %s"%(arg,self.items[arg]) if self.items[arg]!='Null' else "%s"%arg for arg in self.items]
        return "\n".join(l)    
    
def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command,stdout=subprocess.PIPE) == 0
def colored(txt,c='green'):
    if c=='red':
        return f"{Fore.RED}%s{Style.RESET_ALL}"%txt
    else:
        return f"{Fore.GREEN}%s{Style.RESET_ALL}"%txt
def test_all():
    print("will test BE-CCR devices; ")
    for h in ips_ccr:
        print("\t%s"%h)
    print("")
    print("and calib unit devices;")
    for h in ips_calib:
        print("\t%s"%h)
        
    for h in ips_ccr:
        status = colored("OK") if ping(ips_ccr[h]) else colored("NOK",c='red')
        print("%s [%s]"%(h,status))
    for h in ips_calib:    
        status = colored("OK") if ping(ips_calib[h]) else colored("NOK",c='red')
        print("%s [%s]"%(h,status))
def test_ccr():
    print("will test BE-CCR devices; ")
    for h in ips_ccr:
        print("\t%s"%h)
    print("")
    for h in ips_ccr:
        status = colored("OK") if ping(ips_ccr[h]) else colored("NOK",c='red')
        print("%s [%s]"%(h,status))
def test_calib():
    print("will test Calib. unit devices; ")
    for h in ips_calib:
        print("\t%s"%h)
    print("")
    for h in ips_calib:
        status = colored("OK") if ping(ips_calib[h]) else colored("NOK",c='red')
        print("%s [%s]"%(h,status))
def help():
    print("Options; \n")
    print("--test-ccr:\ttest BE-CCR devices Communication")
    print("--test-calib:\ttest Calib. unit devices Communication")
    print("--test-all:\ttest BE-CCR and calib. unit devices Communication")
    print("--ping:\tPing an IP address.")
if '__main__' in __name__:
    args = argument()
    if '--test-ccr' in args:
        test_ccr()
        exit(0)
    if '--test-calib' in args:
        test_calib()
        exit(0)
    if '--test-all' in args:
        test_all()
        exit(0)
    if '--help' in args:
        help()
        exit(0)
    if '--ping' in args:
        ip = args['--ping']
        status = colored("OK") if ping(ip) else colored("NOK",c='red')
        print("%s [%s]"%(ip,status))
        exit(0)