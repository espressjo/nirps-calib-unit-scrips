#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 08:55:49 2022

@author: noboru
"""

from matplotlib import pyplot as plt
import seaborn as sns
from ndfilterlog import cfgfile
from os import listdir
from sys import argv
from os.path import join,basename
import pandas as pd
from datetime import datetime
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

    
def ls_data():
    cfg = cfgfile()
    lpath = cfg['logpath']    
    ls = [ f for f in listdir(lpath) if all(['select' in f,'.csv' in f,'2022' in f])]    
    datetime = [ f.split('.')[2] for f in ls if len(f.split('.')) >2 ]
    sortED = sorted(zip(datetime,ls))
    _,sorted_ls = zip(*sortED)
    return sorted_ls
def find_last():
    cfg = cfgfile()
    lpath = cfg['logpath']    
    ls = ls_data()   

    if len(ls)>0:
        return join(lpath,ls[-1])
    else:
        return ''

def plot(lfile):
    def get_info(lfile):
        #select%d.pos%d.%s.csv
        _tmp = basename(lfile)
        select = _tmp.split('.')[0].replace('select','')
        pos = _tmp.split('.')[1]
        date = datetime.strptime(_tmp.split('.')[2],"%Y%m%d%H%M%S")
        date = date.strftime("%Y-%m-%dT%H:%M:%S")
        return select,pos,date
    
    
    data = pd.read_csv(lfile)
    sns.set_theme()
    x = data['position'].to_numpy()
    y = data['flux'].to_numpy()
    f,ax = plt.subplots()
    ax.plot(x,y,'o',markersize=4)
    select,pos,date = get_info(lfile)
    ax.set(title='Selector %s, position %s\n%s'%(select,pos,date),xlabel='Selector Encoder',ylabel='Flux [W]')
    cfg = cfgfile()
    lpath = cfg['logpath']
    from os import makedirs
    from os.path import isdir

    if not isdir(join(lpath,'graph')):
        makedirs(join(lpath,'graph'),exist_ok=True)
    f.savefig(join(join(lpath,'graph'),"%s.png"%basename(lfile).replace('.csv','')))
    plt.show()
def help():
    print("Options are;")
    print('\t--plot-last: plot the last data set found on disk.')
    print('\t--list-data: list data found in cfg file data path')
    print('\t--plot: plot specific data set. (e.g., --plot=this.file)')
if '__main__' in __name__:
    args = argument()
    if '--help' in args:
        help()
        exit()
    if '--plot-last' in args:
        lfile = find_last()
        print(lfile)
        plot(lfile)
        exit()
    if '--list-data' in args:
        for f in ls_data():
            print("%s"%f)
        exit()
    if '--plot' in args:
        lf = args['--plot']
        cfg = cfgfile()
        lpath = cfg['logpath']
        plot(join(lpath,lf))
        exit()
