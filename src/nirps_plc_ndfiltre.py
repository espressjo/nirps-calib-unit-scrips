#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 07:10:09 2022

@author: noboru
"""

from opcua import Client,ua
import traceback
from time import sleep 
from sys import argv
from ndfilterlog import cfgfile

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

class beckoff():
    
    '''
        Class to control/read some device in NIRPS's calibration unit.
        The PLC must be visible on the network.
        Usefull methods are;
            *connect - open a connection with PLC (It is better to use with -- as --... statement)\n
            *close - close a connection with PLC\n
            *read_NDFilter - read ND filter position\n
            *set_NDFilter - set a ND filter to position\n
            *selector_position - return selector position
            *set_selector - set selector
            
    '''
    def __init__(self,ip,hwsimul=False,port=4840):
        self.simul = hwsimul
        self.simul_pos = 90.0
        self.ip_addr = ip#134.171.102.126 in LaSilla
        self.port = port#PLC comm port is usually 4840
        self.beck = None
        #PLC variables use to read/write selector and filter wheel position
        self.selector_node = 'MAIN.Selector%d.stat.lrPosActual' 
        self.node_select_lrposition = 'MAIN.Selector%d.ctrl.lrPosition' #node to change the lrPosition of Filter 1 or 2
        self.node_select_nCommand = 'MAIN.Selector%d.ctrl.nCommand' #node to change the nCommand of Filter 1 or 2
        self.node_select_bExecute = 'MAIN.Selector%d.ctrl.bExecute' #node to change the bExecute of Filter 1 or 2       
        self.node_actual_pos = 'MAIN.Filter%d.stat.lrPosActual' #node to read a Filter# variable (stat)
        self.node_lr_position = 'MAIN.Filter%d.ctrl.lrPosition' #node to change the lrPosition of Filter 1 or 2
        self.node_nCommand = 'MAIN.Filter%d.ctrl.nCommand' #node to change the nCommand of Filter 1 or 2
        self.node_bExecute = 'MAIN.Filter%d.ctrl.bExecute' #node to change the bExecute of Filter 1 or 2

    def selector_position(self,sNb):
        '''
        Read selector position

        Parameters
        ----------
        sNb : INT
            Selector number.

        Returns
        -------
        FLOAT
            Position

        '''
        if self.simul:
            return self.simul_pos
        val1 = self.beck.get_node("ns=4; s=%s"%(self.selector_node%sNb)).get_value()
        out = str(val1).strip()
        if isinstance(out,str):
            return float(out)
        else:
            return None
    def connect(self):
        '''
        Open a connection with the PLC. Must be called 1st. If with 
        statement is used, no need to use this function.

        Returns
        -------
        None.

        '''
        if self.simul:
            print('Connected to simulatec beckoff')
            return
        self.beck = Client("opc.tcp://%s:%d"%(self.ip_addr,self.port))
        self.beck.connect()
        root=self.beck.get_root_node()
        print(":::::root:::::")
        print(root)
        objects = self.beck.get_objects_node()
        print(":::::objects:::::")
        print(objects)
        child = objects.get_children()
        print(":::::child:::::")    
        print(child)
    def read_NDFilter(self,filter_nb):
        '''
        This function will return the value (str format) of varible [var] of ND filter # [filter_nb]

        Parameters
        ----------
        filter_nb : int
            ND filter number [1,2]
        Returns
        -------
        FLOAT
            return position, or none if hardware failed.

        '''
        if self.simul:
            return self.simul_pos
        val1 = self.beck.get_node("ns=4; s=%s"%(self.node_actual_pos%filter_nb)).get_value()
        out = str(val1).strip()
        if isinstance(out,str):
            return float(out)
        else:
            return None
    def disconnect(self):
        '''
        Close opcua connection with NIRPS PLC.

        Returns
        -------
        None.

        '''
        if self.simul:
            return
        self.beck.disconnect()
        return

    def set_NDFilter(self,filter_nb,pos):
        '''
        Set a ND filter to position. The position of the selector will be monitered
        every second, once the requested position as a difference of less than 1 with
        the requested position, a 5 seconds sleep is called to make sure the requested
        position is reached.

        Parameters
        ----------
        filter_nb : INT
            ND filter number.
        pos : INT
            Selected position.

        Returns
        -------
        INT
            position display in PLC

        '''
        if self.simul:
            self.simul_pos = pos
            return self.simul_pos
        if filter_nb!=1 and filter_nb!=2:
            print("filter_nb must be 1 or 2")
            return
        
        dv = ua.DataValue(ua.Variant(float(pos), ua.VariantType.Double))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_lr_position%filter_nb))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(int(3), ua.VariantType.Int32))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_nCommand%filter_nb))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_bExecute%filter_nb))
        var.set_data_value(dv)        
               
        #check if position is reached
        timer = 0
        for i in range(60):
            sleep(1)
            timer+=1
            if (abs(self.read_NDFilter(filter_nb)-pos)<1):
                sleep(5)#to be really sure we reached the position, we could tune (<1) and this sleep
                timer+=5
                break
        rpos = self.read_NDFilter(filter_nb)
        print("The position ask is %f"%pos)
        print("Position %f reached in %fs."%(rpos,timer))
        return rpos
    def set_selector(self,selector,pos):
        '''
        Set a ND filter to position

        Parameters
        ----------
        selector : INT
            Selector number.
        pos : INT
            Selected position.

        Returns
        -------
        INT
            Selector position display in PLC
            
        '''
        if self.simul:
            self.simul_pos = pos
            return self.simul_pos
        if selector!=1 and selector!=2:
            print("filter_nb must be 1 or 2")
            return
        
        dv = ua.DataValue(ua.Variant(float(pos), ua.VariantType.Double))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_select_lrposition%selector))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(int(3), ua.VariantType.Int32))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_select_nCommand%selector))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_select_bExecute%selector))
        var.set_data_value(dv)        
        sleep(10)   
        timer = 0
        for i in range(60):
            sleep(1)
            timer+=0
            if abs(self.selector_position(selector)-pos)<1:
                sleep(5)
                timer+=5
                break
        rpos = self.selector_position(selector)
        print("The position ask is %f"%pos)
        print("Position %f reached in %fs."%(rpos,timer))
        return rpos

    def __enter__(self):
        '''
        Since connection to hardware is made, its better to use with statement i.e., with beckoff("192.168.62.150") as beck: ...

        Returns
        -------
        SELF
        '''
        if self.simul:
            return self
        else:
            self.connect()
            return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.simul:
            return True
        self.beck.disconnect()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            # return False # uncomment to pass exception through

        return True
def help():
    print("\n\t:::: Beckoff PLC helper menu ::::\n")
    print('--get-position: get absolute position of a subdevice')
    print('--set-position: Set the position of a subdevice')
    print('--selector1: select selector #1')
    print('--selector2: select selector #2')
    print('--nd-filter1: select filter wheel #1')
    print('--nd-filter2: select filter wheel #2')
    print('--ip: set PLC ip address for this script')
    print('--port: set PLC communication port for this script.')
    print('--test-hardware: test if we can connect to beckoff PLC hardware.')
    print('--plc-simul: run in simulation')
def get_args_conf():
    '''
    Will check if an argument for port and ip is set, then
    it will check the config file than it will check the 
    default values.

    Returns
    -------
    ip,port

    '''
    args = argument()
    conf = cfgfile()
    if '--ip' in args:
        ip = args['--ip']
    elif 'beckoff-ip' in conf:
        ip = conf['beckoff-ip']
    else:
        ip = "134.171.102.127"
    if '--port' in args:
        p = args['--port']
    elif '--beckoff-port' in conf:
        p = conf['--beckoff-port']
    else:
        p = 4840
    return ip,p
def test_hardware():
    print("Trying to connect to beckoff. If hardware fails you might see a long list of error messages.")
    try:
        ip,p = get_args_conf()
        with beckoff(ip,port=p,hwsimul=False) as beck:
            pos1 = beck.selector_position(1)
        print("Hardware OK")
        
    except:
        print("Hardware test failed")
        
def isFloat(txt):
    if not len(['.' for c in txt])<=1:
        return False
    return all([c.isnumeric() for c in txt if '.' not in c])
if '__main__' in __name__:
    args = argument()
    if '--help' in args:
        help()
        exit()
    if '--test-hardware' in args:
        test_hardware()
        exit(0)
    ip,p = get_args_conf()
    simul = '--plc-simul' in args

    if all(['--selector1' in args,'--set-position' in args]):
        #we want to move selector 1
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            if isFloat(args['--set-position']):
                beck.set_selector(1, float(args['--set-position']))
    elif all(['--selector2' in args,'--set-position' in args]):
        #we want to move selector 2
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            if isFloat(args['--set-position']):
                beck.set_selector(2, float(args['--set-position']))
    elif all(['--selector1' in args,'--get-position' in args]):
        #we want to get position of selector 1
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            print(beck.selector_position(1))
    elif all(['--selector2' in args,'--get-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck:
            print(beck.selector_position(2))
    #samething for nd-filter
    elif all(['--nd-filter1' in args,'--set-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            if isFloat(args['--set-position']):
                #beck.set_selector(1, float(args['--set-position']))
                beck.set_NDFilter(1,int(args['--set-position']))
    elif all(['--nd-filter2' in args,'--set-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            if isFloat(args['--set-position']):
                beck.set_NDFilter(2,int(args['--set-position']))
    elif all(['--nd-filter1' in args,'--get-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            print(beck.read_NDFilter(1))
    elif all(['--nd-filter2' in args,'--get-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck:
            print(beck.read_NDFilter(2))
    