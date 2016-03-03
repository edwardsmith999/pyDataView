import os
import numpy as np
import sys
import math as maths
import glob
#import collections


from serial_cfdfields import *
from headerdata import *
from postproc import PostProc
from pplexceptions import NoResultsInDir 

class Serial_CFD_PostProc(PostProc):

    """ 
        Post processing class for Serial CFD runs
    """

    def __init__(self,resultsdir,**kwargs):
        self.resultsdir = resultsdir
        self.plotlist = {} #collections.OrderedDict
        self.error = {}
        self.name = self.resultsdir.split('/')[-2]

        # Check directory exists before instantiating object and check 
        # which files associated with plots are in directory
        self.potentialfiles = ( "continuum_vbins", "continuum_tau_xx", 
                                "continuum_tau_xy","continuum_tau_yx", 
                                "continuum_tau_yy")

        if (not os.path.isdir(self.resultsdir)):
            print("Directory " +  self.resultsdir + " not found")
            raise IOError
            
        self.fields_present = []
        for fname in self.potentialfiles:
            if (glob.glob(self.resultsdir+fname)):
                self.fields_present.append(fname)
            if (glob.glob(self.resultsdir+fname+'.*')):
                self.fields_present.append(fname.strip().split('.')[0])

        self.fieldfiles1 = list(set(self.fields_present) & set(self.potentialfiles)) 

        try:
            Header1 = Serial_CFD_HeaderData(self.resultsdir)
        except IOError:
            raise NoResultsInDir

        #Velocity
        if 'continuum_vbins' in (self.fieldfiles1):
            d1 = Serial_CFD_vField(self.resultsdir, **kwargs)
            self.plotlist.update({'u':d1})

        #Stress
        if 'continuum_tau_xx' in (self.fieldfiles1):
            M1 = Serial_CFD_StressField(self.resultsdir,
                                        fname='continuum_tau_xx', 
                                        **kwargs)
            self.plotlist.update({'CFD surface Tau_xx':M1})

        if 'continuum_tau_xy' in (self.fieldfiles1):
            M1 = Serial_CFD_StressField(self.resultsdir,
                                        fname='continuum_tau_xy', **kwargs)
            self.plotlist.update({'CFD surface Tau_xx':M1})

        if 'continuum_tau_yx' in (self.fieldfiles1):
            M1 = Serial_CFD_StressField(self.resultsdir,
                                        fname='continuum_tau_yx', **kwargs)
            self.plotlist.update({'CFD surface Tau_xx':M1})

        if 'continuum_tau_yy' in (self.fieldfiles1):
            M1 = Serial_CFD_StressField(self.resultsdir,
                                        fname='continuum_tau_yy', **kwargs)
            self.plotlist.update({'CFD surface Tau_xx':M1})

        if (len(self.plotlist) == 0):
            raise NoResultsInDir 
