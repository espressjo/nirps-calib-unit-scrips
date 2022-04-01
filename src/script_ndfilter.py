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
from time import sleep
from pm100 import pm100
args = argument()
cfg = cfgfile() 
simul = True
ip = cfg['beckoff-ip']#fetch the ip of the beckoff
port = cfg['beckoff-port']

#default value
start_12 =  [92640,92530]#start pos. for ndfilter #1 and #2
stop_12 = [93000,92890]#stop pos. for ndfilter #1 and #2
steps = 360#number of step (degree)
def mov2pos(ndf,pos):
    '''
    Make sure the 1st position is reached before starting the script.
    Due to harcoded timeout, it may happen that the ND filter don't
    reach the position before the timeout.

    '''
    OK = True
    print("ND filter target position is %f"%pos)
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        beck.set_ndfilter_velocity(ndf)
        while(OK):
            beck.set_ndfilter(ndf, pos)
            newpos = beck.get_ndfilter(ndf)
            OK = 'no' in input("Position %f reached. Is this the right position ? [yes/no]"%newpos)
def selector_mov2pos(select,pos):
    '''
    Make sure the 1st position is reached before starting the script.
    Due to harcoded timeout, it may happen that the selector don't
    reach the position before the timeout.

    '''
    OK = True
    print("Selector target position is %f"%pos)
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        beck.set_selector_velocity(select)
        while(OK):
            beck.set_selector(select, pos)
            newpos = beck.get_selector(select)
            OK = 'no' in input("Position %f reached. Is this the right position ? [yes/no]"%newpos)
def check_tungsten():
    if 'yes' in input("Does the Tungsten lamp is already open since at least 10 minutes? [yes/no]"):
        return
    input('The Tungsten lamp will open now. A 10 minutes timeout will be started. <press any key>')
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        beck.open_tungsten()
    for i in range(10):
        print("%d minutes left"%(10-i))
        sleep(60)
    return 
def get_selector_position(name,selector):
    import pandas as pd
    data = pd.read_csv('../selector-position.csv')
    for i in range(len(data['name'])):
        if name in data['name'][i]:
            return data['selector%d'%selector][i]  

def run(ndf,start,stop,steps):
    from pm100 import pm100
    log = nd_log(ndf)
    positions = linspace(start,stop,steps+1,dtype=int)
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        with pm100(simulation=simul) as pm100:
            for p in positions: 
                beck.set_ndfilter(ndf, p)
                pos = beck.get_ndfilter(ndf)
                flux = pm100.measure()
                log.log(pos, flux)
def help():
    print("Script HELPER!!!")
    print('--steps: number of steps. Defaulted to 360')
    print("--start: starting enconder value")
    print("--stop: stoping enconder value")    
    print('--list-encoder-default: List the start/stop encoder value for both filter wheel')
    #print('--run: start the ndfilter')
    print('--ndfilter1: Select filter #1')
    print('--ndfilter2: Select filter #2')
if '__main__' in __name__:
    args = argument()
    if '--help' in args:
        help()
        exit(0)   
    if '--list-encoder-default' in args:
        print('\tndfilter #1: start: %d, stop: %d'%(start_12[0],stop_12[0]))
        print('\tndfilter #2: start: %d, stop: %d'%(start_12[1],stop_12[1]))
        exit(0)
    #some checkout
    ndf = 1 if '--ndfilter1' in args else 2#select the right NDfilter/selector
    if all(['--ndfilter1' not in args,'--ndfilter2' not in args]):
        help()
        exit(0)
    start = args['--start'] if '--start' in args else start_12[ndf-1]
    stop  = args['--stop']  if '--stop'  in args else stop_12[ndf-1]
        
    
    if '--steps' in args:
        steps = args['--steps']
    
    
    
    #main script logic
    check_tungsten()#check if the tungsten lamp is open
    input('Selector %d will now move to DARK position. <press any key>'%ndf)
    select_p = get_selector_position('DARK',ndf)
    selector_mov2pos(ndf,select_p)
    #we now put the filter wheel approx. to a hign ND level.
    input('We will now set the filter wheel to a high ND level. <press any key>')
    mov2pos(ndf, 92930 if ndf==1 else 92880)#guess the high ND position
    input('We will calibrate the power meter. Make sure it is dark in the room. <press any key>')
    with pm100(simulation=simul) as PM:
        PM.zero_adjust()
    input('Power meter is now calibrated. The selector will now be moved to the Tungsten position. <Press any key>' )
    select_p = get_selector_position('TUN',ndf)
    selector_mov2pos(ndf,select_p)
    input('The ND filter wheel will now be moved to %d. <Press any key>'%start)
    mov2pos(ndf, start)#make sure we are at the right statirng position.    
    run(ndf,start,stop,steps)
    from analyse_ndfilter import get_last,plot_filtred_flux,plot_fit
    f = get_last()
    plot_filtred_flux(f)
    plot_fit(f)    