#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 14:03:52 2022

@author: noboru
"""
from sys import argv
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