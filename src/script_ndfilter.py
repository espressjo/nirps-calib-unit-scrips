#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 06:59:07 2022

@author: noboru
"""

from nirps_plc_ndfiltre import beckoff,argument

from numpy import linspace
from os.path import join
from datetime import datetime
from ndfilterlog import cfgfile,nd_log
from arguments import argument

args = argument()
cfg = cfgfile() 
simul = True
ip = cfg['beckoff-ip']#fetch the ip of the beckoff
port = cfg['beckoff-port']


def mov2pos(ndf,pos):
    '''
    Make sure the 1st position is reached before starting the script.
    Due to harcoded timeout, it may happen that the ND filter don't
    reach the position before the timeout.

    '''
    OK = True
    print("Target position is %f"%pos)
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        while(OK):
            beck.set_ndfilter(ndf, pos)
            newpos = beck.get_ndfilter(ndf)
            OK = 'no' in input("Position %f reached. Is this the right position ? [yes/no]"%newpos)
            
def run(ndf,start,stop,steps):
    from pm100 import pm100
    log = nd_log(ndf)
    positions = linspace(start,stop,steps,dtype=int)
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        with pm100(simulation=simul) as pm100:
            for p in positions: 
                beck.set_ndfilter(ndf, p)
                pos = beck.get_ndfilter(ndf)
                flux = pm100.measure()
                log.log(pos, flux)
                
if '__main__' in __name__:
    start =  92640#for nfilter #2 92530 
    stop = 93000# for nfilter #2 92890
    steps = 360
    ndf = 1#which RAF you want to use
    
    mov2pos(ndf, start)#make sure we are at the right statirng position.
    run(ndf,start,stop,steps)
    