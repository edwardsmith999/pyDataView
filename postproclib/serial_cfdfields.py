#! /usr/bin/env python
import numpy as np

from .field import Field
from .serial_cfdrawdata import Serial_CFD_RawData

# ============================================================================
# CFDField base class

class Serial_CFDField(Field):
    
    nhalos = [0, 1, 0]

    def __init__(self,fdir):
        Raw = Serial_CFD_RawData(fdir, self.fname, self.dtype, 
                         self.nperbin)
        Field.__init__(self,Raw)
        self.header = self.Raw.header
        self.axislabels = ['x','y','z']

# ============================================================================
# CFDField derived classes, but calculated by the main code
class Serial_CFD_vField(Serial_CFDField):

    dtype = 'd'
    nperbin = 3

    def __init__(self,fdir,fname='continuum_vbins'):

        self.fname = fname
        Serial_CFDField.__init__(self,fdir)
        self.labels = self.axislabels
        self.nperbin = self.Raw.nperbin
        self.plotfreq = self.Raw.header.continuum_tplot
        assert self.Raw.nperbin > 0
        self.labels = ['u','v','w']

class Serial_CFD_momField(Serial_CFDField):

    dtype = 'd'
    nperbin = 3

    def __init__(self,fdir,fname='continuum_vbins'):

        self.fname = fname
        Serial_CFDField.__init__(self,fdir)
        self.labels = self.axislabels
        self.nperbin = self.Raw.nperbin
        self.plotfreq = self.Raw.header.continuum_tplot
        assert self.Raw.nperbin > 0
        self.labels = ["rhou","rhov","rhow"]

    def read(self,startrec,endrec,**kwargs):

        grid_data = Serial_CFDField.read(self,startrec,endrec,**kwargs)
        density = float(self.Raw.header.rho)
        grid_data = density*grid_data
        return grid_data 

class Serial_CFD_StressField(Serial_CFDField):

    dtype = 'd'
    nperbin = 4

    def __init__(self,fdir,fname='continuum_tau_xy'):

        if (fname in ("continuum_tau_xx", "continuum_tau_xy",
                      "continuum_tau_yx", "continuum_tau_yy")):
            self.fname = fname
            Serial_CFDField.__init__(self,fdir)
            self.labels = ["right", "top",
							"left", "bottom"]
            Serial_CFDField.__init__(self,fdir)
            assert self.Raw.nperbin > 0
            self.nperbin = self.Raw.nperbin
            self.plotfreq = self.Raw.header.continuum_tplot

