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
#
class argument:
    '''
    Small class the reads up the command line argument. 
    Ex: 
        args = argument()
        if '--path' in args:
            path = args['--path']
    '''
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

class beckoff():
    
    '''
        Class to control/read some device in NIRPS's calibration unit.
        The PLC must be visible on the network.
        Usefull methods are;
            *connect - open a connection with PLC (It is better to use with -- as --... statement)\n
            *disconnect - if connect() is used, use disconnect to release the hardware.
            *close - close a connection with PLC\n
            *get_ndfilter - read ND filter position\n
            *set_ndfilter - set a ND filter to position\n
            *get_selector - return selector position
            *set_selector - set selector
            
    '''
    def __init__(self,ip,hwsimul=False,port=4840):
        self.simul = hwsimul
        self.ndfilter_simul_pos = 92540
        self.selector_simul_pos = 90.0
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

    def get_selector(self,sNb):
        '''
        Read selector sNb position

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
            print('Selector %d is at %f'%(sNb,self.selector_simul_pos))
            return self.selector_simul_pos
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
            print('Connected to simulatec beckoff at IP: %s on port: %d'%(self.ip_addr,self.port))
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
    def get_ndfilter(self,filter_nb):
        '''
        This function will return the ndfilter position. 

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
            print('ND filter %d is at psition %d'%(filter_nb,self.ndfilter_simul_pos))
            return self.ndfilter_simul_pos
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

    def set_ndfilter(self,filter_nb,pos):
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
            print('Setting ND filter %d position at %d'%(filter_nb,pos))
            sleep(2)
            self.ndfilter_simul_pos = pos
            print('ND filter %d reached position %d'%(filter_nb,pos))
            return self.ndfilter_simul_pos
        if filter_nb!=1 and filter_nb!=2:
            print("filter_nb must be 1 or 2")
            return

        
        #Modif!!!!!
        #We want to check if the motors are initialized before moving motor
        node_bInitialized = 'MAIN.Filter%d.stat.bInitialised'
        node_bExecute = 'MAIN.Filter%d.ctrl.bExecute'
        node_bEnabled = 'MAIN.Filter%d.stat.bEnabled'
        node_bEnable_ctrl = 'MAIN.Filter%d.ctrl.bEnable'
        node_nCommand = 'MAIN.Filter%d.ctrl.nCommand'
        
        #self.node_bInitialized_selector = 'MAIN.Selector%d.stat.bInitialised'
        #self.node_bEnabled_selector = 'MAIN.Selector%d.stat.bEnabled'
        #self.node_bEnable_selector_ctrl = 'MAIN.Selector%d.ctrl.bEnable'
            
        #check if motor is enable
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bEnabled%filter_nb)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Double))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bEnable_ctrl%filter_nb))
            var.set_data_value(dv)
            
        #check if motor is inititalize
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bInitialized%filter_nb)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            dv = ua.DataValue(ua.Variant(int(1), ua.VariantType.Int32))
            var = self.beck.get_node("ns=4;  s=%s"%(node_nCommand%filter_nb))
            var.set_data_value(dv)
        
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bExecute%filter_nb))
            var.set_data_value(dv)            
        #fin modif
        
        
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
        for i in range(240):
            if i%30==0:
                print('Timeout in %.1f seconds'%(240-i))
            sleep(1)
            timer+=1
            if (abs(self.get_ndfilter(filter_nb)-pos)<0.1):
                sleep(10)#to be really sure we reached the position, we could tune (<1) and this sleep
                timer+=10
                break
        rpos = self.get_ndfilter(filter_nb)
        print("The position ask is %f"%pos)
        print("Position %f reached in %fs."%(rpos,timer))
        return rpos
    def set_ndfilter_velocity(self,filter_nb):
        '''
        Set a ND filter velocity. 

        Parameters
        ----------
        filter_nb : INT
            ND filter number.
        Returns
        -------
        INT
            position display in PLC

        '''
        if self.simul:
            print('Setting ND filter %d velocity to %d '%(filter_nb,10))
            sleep(2)
            
            print('Velocity set')
            return 
        if filter_nb!=1 and filter_nb!=2:
            print("filter_nb must be 1 or 2")
            return

        
        #Modif!!!!!
        #We want to check if the motors are initialized before moving motor
        node_bInitialized = 'MAIN.Filter%d.stat.bInitialised'
        node_bExecute = 'MAIN.Filter%d.ctrl.bExecute'
        node_bEnabled = 'MAIN.Filter%d.stat.bEnabled'
        node_bEnable_ctrl = 'MAIN.Filter%d.ctrl.bEnable'
        node_nCommand = 'MAIN.Filter%d.ctrl.nCommand'
        
        #self.node_bInitialized_selector = 'MAIN.Selector%d.stat.bInitialised'
        #self.node_bEnabled_selector = 'MAIN.Selector%d.stat.bEnabled'
        #self.node_bEnable_selector_ctrl = 'MAIN.Selector%d.ctrl.bEnable'
            
        #check if motor is enable
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bEnabled%filter_nb)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Double))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bEnable_ctrl%filter_nb))
            var.set_data_value(dv)
            
        #check if motor is inititalize
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bInitialized%filter_nb)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            dv = ua.DataValue(ua.Variant(int(1), ua.VariantType.Int32))
            var = self.beck.get_node("ns=4;  s=%s"%(node_nCommand%filter_nb))
            var.set_data_value(dv)
        
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bExecute%filter_nb))
            var.set_data_value(dv)            
        #fin modif
        
        
        dv = ua.DataValue(ua.Variant(float(10), ua.VariantType.Double))
        var = self.beck.get_node("ns=4;  s=%s"%("MAIN.Filter%d.ctrl.lrVelocity"%filter_nb))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(int(3), ua.VariantType.Int32))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_nCommand%filter_nb))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_bExecute%filter_nb))
        var.set_data_value(dv)        
               
        #check if position is reached
        sleep(10)
        
        print("Velocity Set")
        return 
    def open_tungsten(self):
        '''
        Close the thungsten lamp
        Returns
        -------
        None.

        '''
        if self.simul:
            print('Tungsten opened')
            return
        node_bInitialized = 'MAIN.Tungsten1.stat.bInitialised'
        node_nCommand = 'MAIN.Tungsten1.ctrl.nCommand' 
        node_bExecute = 'MAIN.Tungsten1.ctrl.bExecute'
        
        #check if motor is inititalize
        print('Checking if tungsten lamp is initialized')
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bInitialized)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            print('Initializing tungsten lamp.')
            dv = ua.DataValue(ua.Variant(int(1), ua.VariantType.Int32))
            var = self.beck.get_node("ns=4;  s=%s"%(node_nCommand))
            var.set_data_value(dv)
        
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bExecute))
            var.set_data_value(dv)
        #set some config
        #cfg.nAnalogThreshold = 1
        dv = ua.DataValue(ua.Variant(int(1), ua.VariantType.Int32))
        var = self.beck.get_node("ns=4;  s=%s"%("MAIN.Tungsten1.cfg.nAnalogThreshold"))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(int(0), ua.VariantType.Int32))
        var = self.beck.get_node("ns=4;  s=%s"%("MAIN.Tungsten1.cfg.nMaxOn"))
        var.set_data_value(dv)
        
        #we open the lamp
        
        print('Opening tungsten lamp.')
        dv = ua.DataValue(ua.Variant(int(3), ua.VariantType.Int32))
        var = self.beck.get_node("ns=4;  s=%s"%(node_nCommand))
        var.set_data_value(dv)
    
        dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
        var = self.beck.get_node("ns=4;  s=%s"%(node_bExecute))
        var.set_data_value(dv)
        print('done')
    def close_tungsten(self):
        '''
        Close the thungsten lamp

        Returns
        -------
        None.
        '''
        if self.simul:
            print('Tungsten closed')
            return
        node_bInitialized = 'MAIN.Tungsten1.stat.bInitialised'
        node_nCommand = 'MAIN.Tungsten1.ctrl.nCommand' 
        node_bExecute = 'MAIN.Tungsten1.ctrl.bExecute'
        print('Checking if tungsten lamp is initialized')
        #check if motor is inititalize
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bInitialized)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            print('Initializing tungsten lamp.')
            dv = ua.DataValue(ua.Variant(int(1), ua.VariantType.Int32))
            var = self.beck.get_node("ns=4;  s=%s"%(node_nCommand))
            var.set_data_value(dv)
        
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bExecute))
            var.set_data_value(dv)
        #we close the lamp
        print('Opening tungsten lamp.')
        dv = ua.DataValue(ua.Variant(int(2), ua.VariantType.Int32))
        var = self.beck.get_node("ns=4;  s=%s"%(node_nCommand))
        var.set_data_value(dv)
    
        dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
        var = self.beck.get_node("ns=4;  s=%s"%(node_bExecute))
        var.set_data_value(dv)        
        print('done')
    def set_selector_velocity(self,selector):
        '''
        Set a selector velocity

        Parameters
        ----------
        selector : INT
            Selector number.

        Returns
        -------
        INT
            Selector position display in PLC
            
        '''#MAIN.Selector%d.ctrl.lrVelocity =5
        if self.simul:
            print('Setting selector %d velocity at %f'%(selector,5))
            sleep(2)
            return 
        if selector!=1 and selector!=2:
            print("filter_nb must be 1 or 2")
            return
        
        #Modif!!!!!
        #We want to check if the motors are initialized before moving motor
        node_bInitialized = 'MAIN.Selector%d.stat.bInitialised'
        node_bExecute = 'MAIN.Selector%d.ctrl.bExecute'
        node_bEnabled = 'MAIN.Selector%d.stat.bEnabled'
        node_bEnable_ctrl = 'MAIN.Selector%d.ctrl.bEnable'
        node_nCommand = 'MAIN.Selector%d.ctrl.nCommand'            
        #check if motor is enable
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bEnabled%selector)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Double))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bEnable_ctrl%selector))
            var.set_data_value(dv)
            
        #check if motor is inititalize
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bInitialized%selector)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            dv = ua.DataValue(ua.Variant(int(1), ua.VariantType.Int32))
            var = self.beck.get_node("ns=4;  s=%s"%(node_nCommand%selector))
            var.set_data_value(dv)
        
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bExecute%selector))
            var.set_data_value(dv)            
        #fin modif
        
        
        dv = ua.DataValue(ua.Variant(float(5), ua.VariantType.Double))
        var = self.beck.get_node("ns=4;  s=%s"%("MAIN.Selector%d.ctrl.lrVelocity"%selector))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(int(3), ua.VariantType.Int32))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_select_nCommand%selector))
        var.set_data_value(dv)
        
        dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
        var = self.beck.get_node("ns=4;  s=%s"%(self.node_select_bExecute%selector))
        var.set_data_value(dv)        
        sleep(10)   
        print("Velocity Set")
        return 
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
            print('Setting selector %d position at %f'%(selector,pos))
            sleep(2)
            self.selector_simul_pos = pos
            print('Selector %d reached position %f'%(selector,pos))
            return self.selector_simul_pos
        if selector!=1 and selector!=2:
            print("filter_nb must be 1 or 2")
            return
        
        #Modif!!!!!
        #We want to check if the motors are initialized before moving motor
        node_bInitialized = 'MAIN.Selector%d.stat.bInitialised'
        node_bExecute = 'MAIN.Selector%d.ctrl.bExecute'
        node_bEnabled = 'MAIN.Selector%d.stat.bEnabled'
        node_bEnable_ctrl = 'MAIN.Selector%d.ctrl.bEnable'
        node_nCommand = 'MAIN.Selector%d.ctrl.nCommand'
        
        #self.node_bInitialized_selector = 'MAIN.Selector%d.stat.bInitialised'
        #self.node_bEnabled_selector = 'MAIN.Selector%d.stat.bEnabled'
        #self.node_bEnable_selector_ctrl = 'MAIN.Selector%d.ctrl.bEnable'
            
        #check if motor is enable
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bEnabled%selector)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            dv = ua.DataValue(ua.Variant(True, ua.VariantType.Boolean))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bEnable_ctrl%selector))
            var.set_data_value(dv)
            
        #check if motor is inititalize
        val1 = self.beck.get_node("ns=4; s=%s"%(node_bInitialized%selector)).get_value()
        out = str(val1).strip()
        if 'True' not in out:#if not...
            dv = ua.DataValue(ua.Variant(int(1), ua.VariantType.Int32))
            var = self.beck.get_node("ns=4;  s=%s"%(node_nCommand%selector))
            var.set_data_value(dv)
        
            dv = ua.DataValue(ua.Variant(float(1), ua.VariantType.Boolean))
            var = self.beck.get_node("ns=4;  s=%s"%(node_bExecute%selector))
            var.set_data_value(dv)            
        #fin modif
        
        
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
        timer = 10
        for i in range(240):#2minutes timeout
            if i%30==0:
                print('timeout in %.1f seconds'%(240-timer))
            sleep(1)
            timer+=1
            if abs(self.get_selector(selector)-pos)<0.001:
                sleep(5)
                timer+=5
                break
        rpos = self.get_selector(selector)
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
    print('\t--get-position: get absolute position of a subdevice')
    print('\t--set-position: Set the position of a subdevice')
    print('\t--selector1: select selector #1')
    print('\t--selector2: select selector #2')
    print('\t--nd-filter1: select filter wheel #1')
    print('\t--nd-filter2: select filter wheel #2')
    print('\t--ip: set PLC ip address for this script')
    print('\t--port: set PLC communication port for this script.')
    print('\t--test-hardware: test if we can connect to beckoff PLC hardware.')
    print('\t--plc-simul: run in simulation')
    print('\t--open-tungsten: open tungsten lamp')
    print('\t--close-tungsten: open tungsten lamp')
    print('\t--set-speed-selector: set the speed for device')
    print('\t--set-speed-ndfilter: set the speed for device')
def get_args_conf():
    '''
    Will check if an argument for port and ip is set, then
    it will check the config file. If nothing is found it will
    set to default ip: 134.171.102.127,port: 4840
    default values.

    Returns
    -------
    STR,INT

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
    '''
    This function will try to connect to the hardware and read the position
    of selector #1.

    Returns
    -------
    T if successful, F if we have an hardware problem.

    '''
    print("Trying to connect to beckoff. If hardware fails you might see a long list of error messages.")
    args = argument()
    try:
        ip,p = get_args_conf()
        sim = '--plc-simul' in args
        with beckoff(ip,port=p,hwsimul=sim) as beck:
            pos1 = beck.get_selector(1)
        print("Hardware OK")
        return True
    except:
        print("Hardware test failed")
        return False
def isFloat(txt):
    if len(['.' for c in txt if '.' in c])>1:
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
            print(args['--set-position'])
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
            print(beck.get_selector(1))
    elif all(['--selector2' in args,'--get-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck:
            print(beck.get_selector(2))
    #samething for nd-filter
    elif all(['--nd-filter1' in args,'--set-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            if isFloat(args['--set-position']):
                #beck.set_selector(1, float(args['--set-position']))
                beck.set_ndfilter(1,int(args['--set-position']))
    elif all(['--nd-filter2' in args,'--set-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            if isFloat(args['--set-position']):
                beck.set_ndfilter(2,int(args['--set-position']))
    elif all(['--nd-filter1' in args,'--get-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck: 
            print(beck.get_ndfilter(1))
    elif all(['--nd-filter2' in args,'--get-position' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck:
            print(beck.get_ndfilter(2))
    elif '--open-tungsten' in args:
        with beckoff(ip,port=p,hwsimul=simul) as beck:
            beck.open_tungsten()
    elif '--close-tungsten' in args:
        with beckoff(ip,port=p,hwsimul=simul) as beck:
            beck.close_tungsten()
    elif all(['--set-speed-selector' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck:
            beck.set_selector_velocity(1 if '--selector1' in args else 2)
    elif all(['--set-speed-ndfilter' in args]):
        with beckoff(ip,port=p,hwsimul=simul) as beck:
            beck.set_selector_velocity(1 if '--ndfilter' in args else 2)
    
    