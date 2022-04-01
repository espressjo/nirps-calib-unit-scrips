#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 07:09:45 2022

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
import numpy as np
from arguments import argument
# class argument:
#     '''
#     Small class the reads up the command line argument. 
#     Ex: 
#         args = argument()
#         if '--path' in args:
#             path = args['--path']
#     '''
#     def __init__(self):
#         self.items = {}
#         for arg in argv:
#             if '=' in arg:
#                 self.items[arg.split('=')[0]] = arg.split('=')[1]
#             else:
#                 self.items[arg] = 'Null'
#     def __contains__(self, item):
#         return item in self.items
#     def __getitem__(self, item):
#         if item in self.items:
#             return self.items[item]
#         else:
#             None
#     def __str__(self):
#         l = ["%s: %s"%(arg,self.items[arg]) if self.items[arg]!='Null' else "%s"%arg for arg in self.items]
#         return "\n".join(l)  
    
def ls_data():
    #return a list of all the ndfilter log from oldest to newest
    cfg = cfgfile()
    lpath = cfg['logpath']    
    ls = [ f for f in listdir(lpath) if all(['ndfilter' in f,'.csv' in f,'2022' in f,'#' not in f,'lock' not in f])]    
    dtime = [ f.split('.')[1] for f in ls if len(f.split('.')) >1 ]
    
    sortED = sorted(zip(dtime,ls))
    
    _,sorted_ls = zip(*sortED)
    return sorted_ls
def get_last():
    ls = ls_data()
    cfg = cfgfile()
    p = cfg['logpath']
    if len(ls)>0:
        return join(p,ls[-1])
    else:
        return ''
def help():
    print('Script HELP!!')
    print('\t--list-data: lost all data')
    print('\t--plot-last: plot last log file')
    print('\t--plot: plot given log')
    print('\t--plot-simple: plot flux of last dataset')
def get_info(fname):
    return basename(fname).split('.')[0].replace('ndfilter','')
def plotsimple(file):
    data = pd.read_csv(file)
    position = data['position'].to_numpy()
    flux = data['flux'].to_numpy()
    f,ax = plt.subplots()
    ax.plot(position,flux,'o',markersize=2)
    ax.set(xlabel='position',ylabel='Flux (uW)',title="ND Filter Wheel %s"%(get_info(file)))
    plt.show()
def plot_filtred_flux(file):#f0 = 92705,f1 = 92960
    #get data
    data = pd.read_csv(file)
    position = data['position'].to_numpy()
    flux = data['flux'].to_numpy()
    f0 = position[0]
    f1 = position[-1]
    #plt.semilogy(flux)
    D = -np.log10(flux/np.max(flux))
    
    # Windows filterinf
    ws = 10
    Df = np.convolve(D, np.ones(ws)/ws, 'same')
  
    f,ax = plt.subplots(3,1,figsize=(12,9))
    ax,ax2,ax3 = ax
    ax.plot(position, D,label='Flux')
    ax.plot(position, Df,label='filtered flux')
    ax.plot([f0,f0], [-1,4], '-k', lw=1)
    ax.plot([f1,f1], [-1,4], '-k', lw=1)
    ax.set(title="ND Filter Wheel %s"%(get_info(file)),xlabel='Position', ylabel='Density')
    #ax.grid(True)
    ax.set_ylim([-0.3,None])
    ax.legend()
    
    ppp  = np.poly1d(np.polyfit(position, D, 10))
    ax2.plot([f0,f0], [-1,4], '-k', lw=1)
    ax2.plot(position, D-Df)
    ax2.plot([f1,f1], [-1,4], '-k', lw=1)
    ax2.plot(position, position*0., '-k', lw=1)
    ax2.set_ylabel('Density residual')
    ax2.set_xlabel('Position')
    ax2.set_ylim([-0.2,0.2])
    
    ax3.plot(position[1:], np.diff(Df))
    ax3.plot([f0,f0], [-1,4], '-k', lw=1)
    ax3.plot([f1,f1], [-1,4], '-k', lw=1)
    ax3.plot(position, position*0., '-k', lw=1)
    ax3.set_ylabel('Density residual')
    ax3.set_xlabel('Position')
    ax3.set_ylim([-0.2,0.2])    
    plt.tight_layout()
    
    
    
    plt.show()
def create_ndposition_file(name,x,y):
    cfg = cfgfile()
    p = cfg['logpath']
    f = join(p,basename(name))
def plot_fit(file):
    from scipy.interpolate import interp1d
    data = pd.read_csv(file)
    position = data['position'].to_numpy()
    flux = data['flux'].to_numpy()
    D = -np.log10(flux/np.max(flux))
    f0 = position[0]
    f1 = position[-1]
    # Windows filterinf
    ws = 10
    Df = np.convolve(D, np.ones(ws)/ws, 'same')
    newD = np.arange(0.,3.95,0.1)
    indD = np.argmin(np.abs(Df-newD[:,None]),axis=1)
    newPos = position[indD]
    
    plt.figure(figsize=(15,8))
    plt.plot(position, D)
    plt.plot(position, Df)
    plt.plot(newPos, newD, 'o', ms=7)
    
    plt.plot([f0,f0], [-1,4], '-k', lw=1)
    plt.plot([f1,f1], [-1,4], '-k', lw=1)
    plt.ylabel('Density')
    plt.xlabel('Position')
    plt.title("ND Filter Wheel %s"%(get_info(file)))
    plt.ylim([-0.3,4])
    #save the Nd position file
    
    plt.show()
if '__main__' in __name__:
    args = argument()
    if '--help' in args:
        help()
        exit(0)
    if '--list-data' in args:
        for d in ls_data():
            print(d)
        exit(0)
    if '--plot-last' in args:
        f = get_last()
        plot_filtred_flux(f)
        plot_fit(f)
    if '--plot-simple' in args:
        f = get_last()
        plotsimple(f)
    if '--plot' in args:
        cfg = cfgfile()
        lpath = cfg['logpath']
        ff = args['--plot']
        plot_filtred_flux(join(lpath,ff))
        plot_fit(join(lpath,ff))