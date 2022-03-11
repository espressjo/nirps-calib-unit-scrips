#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 10:26:54 2020

@author: noboru
"""
from telnetlib import Telnet
from time import sleep
from scanf import scanf
import traceback
from datetime import datetime
#TODO logs
class nirps():
    def __init__(self,host,port):
        '''
        Description
            will automatically connect to the HxRG-SERVER
        '''
        self.timefmt ="%Y-%m-%dT" 
        self.port = port
        self.host = host
        
    def connect(self):
        '''
        Initiate a connection with HxRG-SERVER

        Returns
        -------
        None.

        '''
        self.tn = Telnet()
        self.tn.open(self.host,self.port)
        if 'ECHO' not in self.read():
            print("impossible to connect to the server. Cheack your setup.")
            exit(0)
    def _2bytes(self,string):
        '''
        Description
            We must encode every cmd before sending them with telnet
        '''
        return string.encode()
    def _read(self,bytes_msg):
        '''
        Description
            we must decode the output of telnet (from bytes 2 utf-8)
        '''
        return bytes_msg.decode('utf-8').strip()
    def read(self):
        output = self.tn.read_until(b'\n')
        return self._read(output)
    def write(self,msg):
        '''
        Description:
            writes a msg to telnet
        '''
        self.tn.write(self._2bytes(msg))
        return 0
    def simulator(self,state):
        if 'on' in state:
            self.write('simulator state on')
            r = self.read()
            if 'OK' in r and 'NOK' not in r:
                return 0
            else:
                return -1
        elif 'off' in state:
            self.write('simulator state off')
            r = self.read()
            if 'OK' in r and 'NOK' not in r:
                return 0
            else:
                return -1
        else:
            print("wrong choice of argument")
            return -1
    def getId(self):
        self.write("GETUNIQUEID")
        output = self.read()
        if 'OK' not in output:
            return -1
        else:
            _out = scanf("OK %d",output)
            if _out:
                return _out[0]
            else:
                return -1
    def close(self):
        self.tn.close()
    def acqStatus(self):
        '''
            1-> in acquisition
            0-> not in acquisition
            -1-> problem
        '''
        self.write("acqStatus")
        txt = self.read()
        if 'OK' not in txt:
            return -1
        elif 'OK 0' in txt:
            return 0
        elif 'OK 1' in txt:
            return 1
        else:
            return -1
    def setParam(self,**kwargs):
        err = 0
        if 'read' in kwargs:
            r = int(kwargs.get('read'))
            self.write('setParam read %d'%r)
            
            
            if 'NOK' in self.read():
                err+=1
            else:
                print('read set to %d'%r)
        if 'ramp' in kwargs:
            r = int(kwargs.get('ramp'))
            self.write('setParam ramp %d'%r)
            if 'NOK' in self.read():
                err+=1
            else:
                print('ramp set to %d'%r)
        if 'reset' in kwargs:
            r = int(kwargs.get('reset'))
            self.write('setParam reset %d'%r)
            if 'NOK' in self.read():
                err+=1
            else:
                print('reset set to %d'%r)
        if 'drop' in kwargs:
            r = int(kwargs.get('drop'))
            self.write('setParam drop %d'%r)
            if 'NOK' in self.read():
                err+=1
            else:
                print('drop set to %d'%r)
        if 'group' in kwargs:
            r = int(kwargs.get('group'))
            self.write('setParam group %d'%r)
            if 'NOK' in self.read():
                err+=1
            else:
                print('group set to %d'%r)
        if err==0:
            return 0
        else:
            return -1
    def get_status(self):
        
        self.write('GETSTATUS')
        
        if 'OK 1' not in self.read():
            return -1
        else:
            return self.read()
    def start(self):
        '''
        Trigger an acquisition.

        Returns
        -------
        list
            list of unique identification number, if something goes wrong
            the list of the completed ramp's ID will be returned.

        '''
        self.write('START')
        r = self.read()
        if 'NOK' in r:
            return []
        else:
            IDs= [];
            t = 0
            while(1):
                sleep(0.5)
                t+=0.5
                out = self.acqStatus()
                ID = self.getId()
                if all([ID!=0,ID not in IDs,t>6]):
                    IDs.append(ID)
                if (out==0 or out ==2):
                    break
                elif (out<0):
                    print("Error occured, exiting acq loop")
                    return IDs
            print("Total acquisition time ~ %2.2f s"%t)
            return IDs
    def init(self,HW_simulation=False):
        '''
        Trigger the hardware - software initialization. If HW_simulation is
        True, the command simulator state on will be sent beforehand.
        
        Parameters:
        -----------
        HW_simulation : bool
            Turn on the hardware simulator
            
        Returns
        -------
        INT
            0 if succesfull
            -1 if not.

        '''
        if HW_simulation:
            if self.simulator('on')!=0:
                print('unable to init')
                return -1
        else:
            if self.simulator('off')!=0:
                print('unable to init')
                return -1
        self.write('init')
        out = self.read()
        print(out)
        if 'OK' not in out:
            return -1
        else:
            return 0
    def __enter__(self):
        '''
        Since connection to hardware is made, its better to use with statement i.e., with beckoff("192.168.62.150") as beck: ...

        Returns
        -------
        SELF
        '''
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        
        self.tn.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            # return False # uncomment to pass exception through

        return True
if '__main__' in __name__:
    

   
    with nirps('localhost',5555) as ni:
        ni.init(HW_simulation=True)
        ni.setParam(read=2,reset=1,ramp=1)
        ni.start()
    
    
    
    
