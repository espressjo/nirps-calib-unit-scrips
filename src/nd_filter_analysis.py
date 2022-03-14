#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 08:07:34 2022

@author: noboru
"""

from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
#sns.set_theme()
file = '../data/ND-filter-log-20220311090853.csv'
def get_data(file):
    
    data = pd.read_csv(file)
    if any(['filter' in h for h in data]):
        if '--' in str(data['Position_filter_1'][0]):
            return 'ND-filter',2,data['Position_filter_2'].to_numpy(),data['Flux'].to_numpy()
        else:
            return 'ND-filter',1,data['Position_filter_1'].to_numpy(),data['Flux'].to_numpy()
    else:
        if '--' in str(data['Position_selector_1'][0]):
            return 'Selector',2,data['Position_selector_2'].to_numpy(),data['Flux'].to_numpy()
        else:
            return 'Selector',1,data['Position_selector_1'].to_numpy(),data['Flux'].to_numpy()


def plot_ndfiltre_flux(file,f0 = 92705,f1 = 92960):
    #get data
    title,nb,position,flux = get_data(file)
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
    ax.set(title="%s #%d"%(title,nb),xlabel='Position', ylabel='Density')
    #ax.grid(True)
    ax.set_ylim([-0.3,None])
    plt.legend()

    ind0 = np.argmin(np.abs(position-f0))
    ind1 = np.argmin(np.abs(position-f1))
    
    ppp  = np.poly1d(np.polyfit(position[ind0:ind1], D[ind0:ind1], 10))
    

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

    from scipy.interpolate import interp1d
    newD = np.arange(0.,3.95,0.1)
    indD = np.argmin(np.abs(Df[ind0:ind1]-newD[:,None]),axis=1)
    newPos = position[ind0:ind1][indD]
    
    plt.figure(figsize=(15,8))
    plt.plot(position, D)
    plt.plot(position[ind0:ind1], Df[ind0:ind1])
    plt.plot(newPos, newD, 'o', ms=7)
    plt.plot([f0,f0], [-1,4], '-k', lw=1)
    plt.plot([f1,f1], [-1,4], '-k', lw=1)
    plt.ylabel('Density')
    plt.xlabel('Position')
    plt.ylim([-0.3,4])
if '__main__' in __name__:
    plot_ndfiltre_flux(file)
    plt.show()
    


