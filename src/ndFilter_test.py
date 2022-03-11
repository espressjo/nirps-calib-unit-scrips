#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  5 09:40:04 2021

@author: Jonathan St-Antoine, jonathan@astro.umontreal.ca
"""

from opcua import Client,ua
import traceback
from os.path import join
from time import sleep 
from datetime import datetime
import numpy as np
from sys import exit
from os import getcwd

#TODO adjust the sleep funtion because the PLC return the value imediately. So the actual position recorded might not be good


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
    def __init__(self,ip,hwsimul=False):
        self.simul = hwsimul
        self.simul_pos = 90.0
        self.ip_addr = ip
        self.port = 4840#PLC comm port 
        self.beck = None
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
  
class nd_filter_test():
    
    def __init__(self,hwsimul=False):
        self.selector_1_position = 70.3#position to shine FP onto detector
        self.selector_2_position = 69.9#position to shine FP onto detector
        self.p = getcwd()
        self.plc_ip = "192.168.62.150"
        self.list_position1 = np.arange(92640,93001,1,dtype=int)
        self.list_position2 = np.arange(92605,92966,1,dtype=int)
        self.simul = hwsimul
    def check_position(self):
        print(":::::::::: NIRPS Selector test ::::::::::\n")
        print('\tBoth ND filter wheel will be moved over the')
        print('\tfull range of the ND. Images will be taken')
        print('\tby the detector. Once finished the data will')
        print('\tbe save here: %s\n'%self.p)
        if 'no' in input('Do you want to proceed? [yes,no]'):
            exit(0)
        with beckoff(self.plc_ip,hwsimul=self.simul) as beck: 
            pos1 = beck.selector_position(1)
            pos2 = beck.selector_position(2)
            if pos1 !=self.selector_1_position or pos2 !=self.selector_2_position:
                print("\t:::::::::::::::::::::::::::")
                print("\t::        Warning        ::")
                print("\t:::::::::::::::::::::::::::\n")
                print("\tThe current position of selector 1 or 2 seems to ")
                print("\tbe off. We expect selector 1 to be at position %f,"%self.selector_1_position)
                print("\tbut the current position is %f"%pos1)            
                print("\te expect selector 2 to be at position %f,"%self.selector_2_position)
                print("\tbut the current position is %f\n"%pos2)
        if 'no' in input("Do you want to proceed? [yes/no]"):
            exit(0)
    def log(self,position,uniqueid):
        with open(join(self.p,self.lfile),'a') as f:
            dt = datetime.utcnow()
            time = dt.strftime("%Y-%m-%dT%H:%M:%S")
            f.write("%s,%f,%d\n"%(time,position,uniqueid))
    def run(self,pos):
        from nirps_scripting_class import nirps
        
        self.check_position()    
        nirps = nirps('localhost',5555)
        nirps.init(HW_simulation=self.simul)
        nirps.setParam(read=5,ramp=1)
        dt = datetime.utcnow()
        self.lfile = 'ND%d_%s.log'%(pos,dt.strftime("%Y-%m-%dT%H:%M:%S"))
        if pos==1:
            ls = self.list_position1
        else:
            ls = self.list_position2
        with beckoff(self.plc_ip,hwsimul=self.simul) as beck:
            
            for p in ls:
                tpos = beck.set_NDFilter(pos,p)
                ids = nirps.start()
                print(ids)
                if len(ids)>=1:
                    ID = ids[0]
                else:
                    ID = -1
                self.log(tpos,ID)
                
            
if '__main__' in __name__:
    ndft = nd_filter_test(hwsimul=True)#turn on and off the hardware simulation 
    #testing purposes
    #ndft.list_position1 = np.arange(92640,93001,40)
    ndft.list_position2 = np.arange(92605,92966,40)
    ndft.run(2)
    


            
    
    
    