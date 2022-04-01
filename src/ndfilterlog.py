#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 07:20:45 2022

@author: noboru
"""
import os
import re
from datetime import datetime

class cfgfile:
    def __init__(self):
        self.cfg = {}
        self.lfile = '../ndfilter.cfg'
        if 'USERPROFILE' in os.environ:
            #we're running on Windows
            self.desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        else:
            #we're running on Linux
            self.desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
        self.cfg['logpath'] = self.desktop
        self.cfg['pm100-avg'] = 1000
        self.cfg['nb-read'] = 5
        self.cfg['selector-inc'] = 40
        self.cfg['beckoff-ip'] = '134.171.102.126'
        self.cfg['beckoff-port'] = 4840
        if not os.path.isfile(self.lfile):
            print('No configuration file found. Default values will be used.')
            return 
        else:
            self.parse()
            return 
    def __contains__(self, item):
        return item in self.cfg
    def __getitem__(self,items):
        if items in self.cfg:
            return self.cfg[items]
    def get_cfg_file(self):
        return self.cfg
    def isFloat(self,txt):
        return all([t.isnumeric() for t in txt if t!='.'])
    def isIP(self,txt):
        if '.' not in txt:
            return False
        if not len(['.' for c in txt if '.' in c])==3:
            return False
        return all([c.isnumeric() for c in txt if c!='.'])
    def morph(self,txt:str):
        if txt.isnumeric():
            return int(txt)
        elif self.isIP(txt):
            return str(txt)
        elif self.isFloat(txt):
            return float(txt)
        return txt
    def parse(self):
        #parsing cfg file
        with open(self.lfile,'r') as f:
            lines = f.readlines()
        lines = [line.split('#')[0] if '#' in line else line for line in lines]
        lines = [line.strip() for line in lines if len(line)>3]
        lines = [re.sub(r'\s+', ' ', line) for line in lines if line]
        for line in lines:
            self.cfg[line.split(' ')[0].lower()] = self.morph(line.split(' ')[1])
        
    def __str__(self):
        STR = ["%s %s\n"%(h,str(self.cfg[h])) for h in self.cfg]
        return "".join(STR)
class nd_log:
    def __init__(self,ndfilter_nb):
        self.fmt = "%Y%m%d%H%M%S"
        if ndfilter_nb<1 or ndfilter_nb>2:
            print('ndfilter_nb must be 1 or 2')
        self.nd = ndfilter_nb
        self.make_file()#create the log file with header
    def make_file(self):
        cfg = cfgfile()
        p = cfg['logpath']
        self.fname = "ndfilter%d.%s.csv"%(self.nd,datetime.now().strftime(self.fmt))
        self.fname = os.path.join(p,self.fname)
        with open(self.fname,'a') as f:
            f.write('position,flux\n')
        return self.fname
    def log(self,pos,flux):
        with open(self.fname,'a') as f:
            f.write('%d,%.9f\n'%(pos,flux)) 
# class nd_filter_log:
#     def __init__(self,):
        
#         self.dtfmt = "%Y-%m-%dT%H:%M:%S"
#         self.lffmt = "ND-filter-log-%Y%m%d%H%M%S.csv"
#         cfg = cfgfile()
#         self.path = cfg.cfg['logpath']
#         if not os.path.isdir(self.path):
#             print("path: %s does not exist. No log will be saved."%self.path)
#         self.lfile = datetime.now().strftime(self.lffmt)
#         self.make_header()
#         print("Log will be saved here: %s"%(os.path.join(self.path,self.lfile)))
#     def log_selector_1_flux(self,pos,f):
#         with open(os.path.join(self.path,self.lfile),'a') as ff:
#             ff.write("%s,%s,%s,%s,%s,%s\n"%(datetime.now().strftime(self.dtfmt),
#                                            datetime.utcnow().strftime(self.dtfmt),
#                                            str(pos),
#                                            '--',
#                                            str(f),
#                                            '--'))
#     def log_selector_2_flux(self,pos,f):
#         with open(os.path.join(self.path,self.lfile),'a') as ff:
#             ff.write("%s,%s,%s,%s,%s,%s\n"%(datetime.now().strftime(self.dtfmt),
#                                            datetime.utcnow().strftime(self.dtfmt),
#                                            '--',
#                                            str(pos),
#                                            str(f),
#                                            '--'))
#     def log_selector_1_det(self,pos,f):
#         with open(os.path.join(self.path,self.lfile),'a') as ff:
#             ff.write("%s,%s,%s,%s,%s,%s\n"%(datetime.now().strftime(self.dtfmt),
#                                            datetime.utcnow().strftime(self.dtfmt),
#                                            str(pos),
#                                            '--',
#                                            '--',
#                                            str(f)))   
#     def log_selector_2_det(self,pos,f):
#         with open(os.path.join(self.path,self.lfile),'a') as ff:
#             ff.write("%s,%s,%s,%s,%s,%s\n"%(datetime.now().strftime(self.dtfmt),
#                                            datetime.utcnow().strftime(self.dtfmt),
#                                            '--',
#                                            str(pos),
#                                            '--',
#                                            str(f)))
#     def make_header(self):
#         with open(os.path.join(self.path,self.lfile),'w') as f:
#             f.write('Datetime(local),Datetime(UTC),Position_select_1,Position_select_2,Flux,UID\n')
            
if '__main__' in __name__:
    cfg = cfgfile()
    cfgf = cfg.get_cfg_file()
# class nd_filter_log:
#     def __init__(self):
#         self.path = os.path.getcwd()
