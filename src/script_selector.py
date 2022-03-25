#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 07:32:54 2022

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
simul = True
ip = cfg['beckoff-ip']#fetch the ip of the beckoff
port = cfg['beckoff-port']

def log(fname,pos,flux):
    cfg = cfgfile()
    path = cfg['logpath']
    with open(join(path,fname),'a') as f:
        f.write('%f,%f\n'%(pos,flux))
def make_name(selector,start,stop,steps,position_name):
    #mid = linspace(start,stop,steps,dtype=int)[int(steps/2)]
    time = datetime.now().strftime(fmt)
    cfg = cfgfile()
    fname = "select%d.%s.%s.csv"%(selector,position_name,time)
    with open(join(cfg['logpath'],fname),'a') as f:
        f.write('position,flux\n')
    return fname

def mov2pos(selector,pos):
    '''
    Make sure the 1st position is reached before starting the script.
    Due to harcoded timeout, it may happen that the selector don't
    reach the position before the timeout.

    '''
    OK = True
    print("Target position is %f"%pos)
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        beck.set_selector_velocity(selector)
        while(OK):
            beck.set_selector(selector, pos)
            newpos = beck.get_selector(selector)
            OK = 'no' in input("Position %f reached. Is this the right position ? [yes/no]"%newpos)
            
def run(select,start,stop,steps,position_name):
    positions = linspace(start,stop,steps)
    lname = make_name(select,start,stop,steps,position_name)#create the log
    from pm100 import pm100
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        
        with pm100(simulation=simul) as pm100:
            for p in positions:
                beck.set_selector(select, p)
                pos = beck.get_selector(select)
                flux = pm100.measure()                
                log(lname,pos,flux)
def get_position(name,selector):
    import pandas as pd
    data = pd.read_csv('../selector-position.csv')
    for i in range(len(data['name'])):
        if name in data['name'][i]:
            return data['selector%d'%selector][i]            
def open_tungsten():
    print('opening tungsten lamp...')
    with beckoff(ip,hwsimul=simul,port=port) as beck:
        beck.open_tungsten()
    from time import sleep
    for i in range(10):
        print("%d minutes left"%(10-i))
        sleep(60)
    print('Tungsten open.')
    
def help():
    print("script HELP!!!")
    print('--selector1: run script for selector 1')
    print('--selector2: run script for selector 2')
    print('--position: Selector position; UN2,UN1,TUN,FP,LFC,DARK')
    print('--steps: number of steps for scanning')
    print('--width: width of the scan')
    print('--open-tungsten: Open Tungsten lamp with a timer.')
if '__main__' in __name__:
    pos_choice = ['UN2','UN1','TUN','FP','LFC','DARK']
    if len(argv)==1:
        #run this script for; 
        selector = 2 
        position_name = 'LFC'#choice are; UN2,UN1,TUN,FP,LFC,DARK
        mid = get_position(position_name,selector)
        width = 1
        steps = 100
        
        #set a few things
        start_position = mid-width/2.
        stop_position = mid+width/2.    
        mov2pos(selector,mid)
        run(selector,start_position,stop_position,steps,position_name)
        print("Script done")
        #show the graphs
        from analyse_selector import plot,find_last
        plot(find_last())
    if '--help' in args:
        help()
        exit(0)
    if '--open-tungsten' in args:
        open_tungsten()
    if '--selector1' in args:
        select=1
    elif '--selector2' in args:
        select=2 
    else:
        print("Must specify which selector you want.")
        help()
        exit(0)
    if '--position' not in args:
        print("Must specify a position.")
        help()
        exit(0)
    pos = args['--position']
    if pos not in pos_choice:
        print("Positions are;")
        for p in pos_choice:
            print('\t%s'%p)
            exit(0)
    #with all that lets run the script
    #run this script for; 
    selector = select 
    position_name = pos #choice are; UN2,UN1,TUN,FP,LFC,DARK
    mid = get_position(position_name,selector)
    width = float(args['--width']) if '--width' in args else 1
    steps = int(args['--steps']) if '--steps' in args else 100

    input('The script is about to start. Make sure the Tungsten fiber is in the %s of selector %d.\n<Press any key to continue>'%(position_name,selector))
    #set a few things
    start_position = mid-width/2.
    stop_position = mid+width/2.    
    mov2pos(selector,mid)
    run(selector,start_position,stop_position,steps,position_name)
    print("Script done")
    #show the graphs
    from analyse_selector import plot,find_last
    plot(find_last())
    
    
    