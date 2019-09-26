#!/usr/bin/env python
import numpy as np
import scipy as sp

class MacroProps:
    
    def __init__(self,fdir):
        self.macro = np.genfromtxt(fdir+'/macroscopic_properties',
                                   delimiter=';', names=True)
    def get(self,string):
        return self.macro[string]

    def get_mean(self,string,start=1000):
        return np.mean(self.macro[string][start:])

    def get_std(self,string,start=1000):
        return np.std(self.macro[string][start:])

    def get_stderror(self,string,start=1000):
        s = np.std(self.macro[string][start:])
        n = self.macro[string][start:].shape[0]
        return np.divide(s,np.sqrt(n))

if __name__ == "__main__":
    obj = MacroProps('./')
    prop = 'Pressure'
    print(('For ' + prop + ' mean = ' + str(obj.get_mean(prop)) + ' with standard deviation = ' 
		  + str(obj.get_std(prop)) + ' and standard error = ' + str(obj.get_stderror(prop)) ))
