
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 15:40:13 2022

@author: espressjo
"""
# -*- coding: utf-8 -*-

import pyvisa
import numpy as np
import traceback
from ndfilterlog import cfgfile
from sys import argv
from colorama import init
init()
from colorama import Fore,Style

"""
Will try to find the pm100 plugged on the computer. If no device is found
a message will be displayed. If more than 1 device is found, a list will
be displayed and the user will have to make a choice. 
Power measurement are performed and the value is returned in Watts. 

The main method is pm100.measurement() use this. It is recommended to use 
the;
     with ... as ...: format to make sure all resource are properly closed!
     
methods;
    *set_lpass: Set a low pass filter.
    *measurement: Read the photodiode.
    *zero_adjust: Perform a zero adjusment. Make sure the photodiode is covered.
    *set_correction_wavelength: Set a correction wavelength. Used for absolute measurement.
    *close: release the hardware. We recommend using with/as statement.
    
     
"""
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
class pm100:
    def __init__(self,simulation=False):
        self.inst = None
        self.power_meter = None
        self.reasource_manager = None
        self.avg_measurment = 1000
        self.lfrequency = 50
        cfg = cfgfile()
        self.sim = simulation
        if 'pm100-avg' in cfg:
            self.avg_measurment = cfg['pm100-avg']
        self.sensor_idn = 'Unknown' #ID of the sensor plugged in
        self.unit = 'W' #unit of the measurement
        self.measurment_type = 'power' #type of measurment
        
        
        if simulation:
            self.init_sim()
            self.measure = self._measure_sim#main method measure()/return a float
            
        else:
            self.init()
            self.measure = self._measure #main method measure()/return a float
            

        
    def init(self):
        """
        Will initialize the hardware. Set the measurment to power 
        and 1000 avg. read. 

        Returns
        -------
        None.

        """
        from ThorlabsPM100 import ThorlabsPM100
        self.reasource_manager = pyvisa.ResourceManager()
        
        resources = self.reasource_manager.list_resources()
        if len(resources)<1:
            print("No instrument found. Plug and power UP devices.")
            self.reasource_manager.close() 
            exit()
        for _resource in resources:
            print(_resource)
        good_resource = [_resource for _resource in resources if all(['USB' in _resource,'INST' in _resource])]
        
        if len(good_resource)>1:
            print('More than 1 device found.')
            [print("(%d) %s"%(i+1,good_resource[i])) for i in range(len(good_resource)) ]
            selection = input('Make a selection: ')
            resource = good_resource[selection-1]
        else:
            resource = good_resource[0]
            
        
        self.inst = self.reasource_manager.open_resource(resource)
        self.inst.timeout = None
        self.power_meter = ThorlabsPM100(inst=self.inst)
        #set to photometer
        self.power_meter.input.adapter.type ='PHOT'
        self.power_meter.sense.average.count = self.avg_measurment#average 1000 reading by default
        
        self.power_meter.configure.scalar.power()#configure for power measurment
        self.sensor_idn = self.power_meter.system.sensor.idn
        #set the power meter to have lfrequency of 50Hz
        self.power_meter.system.lfrequency = 50
        self.lfrequency = 50
        #print('Initialized')
    def set_lpass(self,state='ON'):
        '''
        Set the low-pass filter On or OFF

        Parameters
        ----------
        state : TYPE, optional
            DESCRIPTION. The default is 'ON'.

        Returns
        -------
        None.

        '''
        if self.sim:
            return
        if 'ON' in state:
            self.power_meter.input.pdiode.filter.lpass.state =1
        else:
            self.power_meter.input.pdiode.filter.lpass.state =0
    def _get_lpass(self):
        #Utility function. This is not meantto be use outside this script.
        if self.power_meter.input.pdiode.filter.lpass.state ==1:
            return 'ON'
        else:
            return 'OFF'
    def init_sim(self):
        '''
        Fake initialization.

        Returns
        -------
        None.

        '''
        self.avg_measurment = 1000
        self.sensor_idn = 'Simulation'
        #print('Initialized')
    def avg(self,_arr):
        #no need for anything more robust. Test for nan (just in case) 
        return np.nanmean(_arr)
    def zero_adjust(self):
        '''
        Perform a zero adjustment. Make sure the sensor is covered.

        Returns
        -------
        None.

        '''
        if self.sim:
            print("New zero value: %1.23E-10")
            return 
        from time import sleep
        print("Current zero value: %.6E"%(self.power_meter.sense.correction.collect.zero.magnitude))
        print("Starting zero adjust, this may take a few seconds.")
        self.power_meter.sense.correction.collect.zero.initiate()
        
        while(self.power_meter.sense.correction.collect.zero.state==1):
            sleep(1)
        print("New zero value: %.6E"%(self.power_meter.sense.correction.collect.zero.magnitude))
    def set_correction_wavelength(self,wl):
        '''
        Will apply a wavelength correction if needed.

        Parameters
        ----------
        wl : FLOAT
            Wavelength.

        Returns
        -------
        None.

        '''
        if self.sim:
            print("New correction wavelength set to %f"%1552.1)
            return
        print("current correction wavelength %f"%self.power_meter.sense.correction.wavelength)
        self.power_meter.sense.correction.wavelength = wl
        print("New correction wavelength set to %f"%self.power_meter.sense.correction.wavelength)

    def __str__(self):
        txt = ""
        txt+="Current zero value: %.6E\n"%(self.power_meter.sense.correction.collect.zero.magnitude)
        txt+="lfrequency: %f\n"%(self.power_meter.system.lfrequency)
        txt+="Sensor: %s\n"%(self.power_meter.system.sensor.idn)
        txt+="Average readout: %d\n"%(self.power_meter.sense.average.count)
        txt+="Correction wavelength: %f\n"%(self.power_meter.sense.correction.wavelength)
        txt+="low pass filter: %s\n"%(self._get_lpass())
        return txt
    def _measure(self):
        return self.power_meter.read
    def _measure_sim(self):
        vals = [np.random.ranf() for i in range(self.avg_measurment)]
        return self.avg(vals)

    def close(self):
        '''
        We recommend using the with ... as ...: statement, but if needed
        one can use this function to release the hardware at the end of 
        a script.

        Returns
        -------
        None.

        '''
        if self.sim:
            return
        if self.reasource_manager:
            self.inst.close()
            self.reasource_manager.close() 
    def __enter__(self):
        '''
        Since connection to hardware is made, its better to use with statement.
        Returns
        -------
        SELF
        '''
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.reasource_manager:
            self.inst.close()
            self.reasource_manager.close()            
            return True
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            # return False # uncomment to pass exception through

        return True
def test_package():
    def colored(txt,c='green'):
        if c=='red':
            return f"{Fore.RED}%s{Style.RESET_ALL}"%txt
        else:
            return f"{Fore.GREEN}%s{Style.RESET_ALL}"%txt
    #pyvisa
    try:
        import pyvisa
        print("%s:\t%s\t[%s]"%('pyvisa',pyvisa.__version__,colored('OK')))
    except:
        print("%s:\tNot installed\t[%s]"%('pyvisa',colored('NOK',c='red')))
    #ThorlabsPM100
    try:
        import ThorlabsPM100
        print("%s:\t%s\t[%s]"%('pyvisa',ThorlabsPM100.__version__,colored('OK')))
    except:
        print("%s:\tNot installed\t[%s]"%('ThorlabsPM100',colored('NOK',c='red')))
        
def help():
    print('\t:::: pm100 Helper ::::\n\n')
    print('\t\t--help: current help')
    print('\t\t--read: make a power readout with pm100.')
    print('\t\t--test-hardware: Test the hardware')
    print('\t\t--test-package: Test the required python package')
    
def test_hardware():
    from ThorlabsPM100 import ThorlabsPM100
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    if len(resources)<1:
        print("No hardware found.")
        return
    print("List of resource found;\n")
    if len(resources)<1:
        print("No instrument found. Plug and power UP devices.")
        rm.close() 
        exit()
    good_resource = [_resource for _resource in resources if all(['USB' in _resource,'INST' in _resource])]
    if len(good_resource)>1:
        print('More than 1 device found.')
        [print("(%d) %s"%(i+1,good_resource[i])) for i in range(len(good_resource)) ]
        selection = input('Make a selection: ')
        resource = good_resource[selection-1]
    else:
        resource = good_resource[0]
    print("\nTesting %s\n"%resource)
    inst = rm.open_resource(resource)
    inst.timeout = None
    pm100 = ThorlabsPM100(inst=inst)
    print("Hardware's fine!")
    inst.close()
    rm.close()
    return

if __name__=="__main__":
    
    args = argument()
    if '--help' in args:
        help()
        exit(0)
    if '--read' in args:
        with pm100(simulation=False) as pm:
            print(pm.measure())#averaged of 1000 reads.
    if '--test-package' in args:
        test_package()
        exit(0)
    if '--test-hardware' in args:
        test_hardware()
        
            
        
    
     