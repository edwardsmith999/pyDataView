#! /usr/bin/env python
import numpy as np

from .field import Field
from .cfdrawdata import CFD_RawData

# ============================================================================
# CFDField base class

class CFDField(Field):

    nhalos = [0, 1, 0]

    def __init__(self,fdir):
        Raw = CFD_RawData(fdir)
        Field.__init__(self,Raw)
        self.axislabels = ['x','y','z']
        self.plotfreq = 1

# ============================================================================
# CFDField derived classes, but calculated by the main code
class CFD_vField(CFDField):

    nperbin = 3 

    def __init__(self,fdir):
        CFDField.__init__(self,fdir)
        assert self.Raw.npercell > 0
        self.labels = ['u','v','w']
    
    def read(self,startrec,endrec,binlimits=None,**kwargs):
        subdata = CFDField.read(self,startrec,endrec,binlimits=binlimits,
                                **kwargs) 
        v = subdata[:,:,:,:,0:3]
        return v 
        
class CFD_PField(CFDField):

    nperbin = 1

    def __init__(self,fdir):
        CFDField.__init__(self,fdir)
        assert self.Raw.npercell > 3
        self.labels = ['p']

    def read(self,startrec,endrec,binlimits=None,**kwargs):
        subdata = CFDField.read(self,startrec,endrec,binlimits=binlimits,
                                **kwargs) 
        P = subdata[:,:,:,:,3:4]
        return P 


class CFD_StressField(CFDField):

    nperbin = 9    
    def __init__(self,fdir):
        CFDField.__init__(self,fdir)
        assert self.Raw.npercell > 4
        x = self.axislabels[0]; y = self.axislabels[1]; z = self.axislabels[2]
        self.labels = [x+x,x+y,x+z,
                       y+x,y+y,y+z,
                       z+x,z+y,z+z]

    def read(self,startrec,endrec,binlimits=None,**kwargs):
        subdata = CFDField.read(self,startrec,endrec,binlimits=binlimits,
                                **kwargs) 
        P = subdata[:,:,:,:,4:]
        return P 
# =============================================================================
# Complex fields that require extra calculations. 
class CFD_complexField(CFDField):
    
    def inherit_parameters(self, subfieldobj):
        self.header = subfieldobj.Raw.header
        self.nperbin = subfieldobj.nperbin
        self.cpol_bins = False
        self.plotfreq = subfieldobj.plotfreq
        self.axislabels = subfieldobj.axislabels
        self.labels = subfieldobj.labels


class CFD_mugradvField(CFD_complexField):
  
    nperbin = 9
 
    def __init__(self, fdir):
        self.vField = CFD_vField(fdir)
        CFD_complexField.__init__(self, fdir)
        x = self.axislabels[0]; y = self.axislabels[1]; z = self.axislabels[2]
        self.labels = [x+x,x+y,x+z,
                       y+x,y+y,y+z,
                       z+x,z+y,z+z]
        self.rho = None

    def set_rho(self, rho):
        self.rho = rho
        
    def read(self, startrec, endrec, binlimits=None, **kwargs):

        if (self.rho == None):
            print(('CFD_mugradvField requires rho, set by ' +
                  'CFD_mugradvField.set_rho(rho).'))
 
        vdata = self.vField.read(startrec, endrec, binlimits=binlimits, 
                                 **kwargs)

        # The call to grad between >>> 
        # should do the same as the lines between <<<
        # but I haven't changed it as I can't check over ssh...

        # >>>>>>>>>>>>>>>>>>>>
        #gradv = self.grad(vdata)
        # >>>>>>>>>>>>>>>>>>>>

        # <<<<<<<<<<<<<<<<<<<<
        dx = self.vField.Raw.dx
        dy = self.vField.Raw.dy
        dz = self.vField.Raw.dz
        gradv = np.empty(list(vdata.shape[:-1]) + [9])
        for rec in range(gradv.shape[-2]):
            for ixyz in range(3):
                for jxyz in range(3):
                    c = 3*ixyz + jxyz
                    gradv[:,:,:,rec,c] = (
                        np.gradient(vdata[:,:,:,rec,ixyz], dx, dy, dz)[jxyz]
                    )
        # <<<<<<<<<<<<<<<<<<<<


        nugradv = self.vField.Raw.nu*gradv
        try:
            mugradv = np.multiply(nugradv, self.rho)
            return mugradv
        except TypeError:
            print('Rho not set, returning nugradv')
            return nugradv

class CFD_strainField(CFD_complexField,CFD_vField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = CFD_vField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.labels = ["dudx","dudy","dudz",
                       "dvdx","dvdy","dvdz",
                       "dwdx","dwdy","dwdz"]
        self.nperbin = 9

    def read(self,startrec,endrec, binlimits=None,**kwargs):
        vdata = self.vField.read(startrec, endrec, 
                                 binlimits=None)

        straindata = self.grad(vdata)

        if (binlimits):

            # Defaults
            lower = [0]*3
            upper = [i for i in straindata.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            straindata = straindata[lower[0]:upper[0],
                                    lower[1]:upper[1],
                                    lower[2]:upper[2], :, :]

        return straindata


class CFD_vortField(CFD_complexField,CFD_vField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = CFD_vField(fdir)
        self.strainField = CFD_strainField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.strainField)
        self.labels = ["x","y","z"]
        self.nperbin = 3

    def read(self,startrec,endrec, binlimits=None,**kwargs):
        dudr = self.strainField.read(startrec, endrec, 
                                      binlimits=None)

        vortdata = np.empty([dudr.shape[0],dudr.shape[1],
                             dudr.shape[2],dudr.shape[3],self.nperbin])
        vortdata[:,:,:,:,0] = ( dudr[:,:,:,:,7]
                               -dudr[:,:,:,:,5])
        vortdata[:,:,:,:,1] = ( dudr[:,:,:,:,2]
                               -dudr[:,:,:,:,6])
        vortdata[:,:,:,:,2] = ( dudr[:,:,:,:,3]
                               -dudr[:,:,:,:,1])

        if (binlimits):

            # Defaults
            lower = [0]*3
            upper = [i for i in vortdata.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            vortdata = vortdata[lower[0]:upper[0],
                                lower[1]:upper[1],
                                lower[2]:upper[2], :, :]

        return  vortdata


class CFD_dissipField(CFD_complexField,CFD_vField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = CFD_vField(fdir)
        self.strainField = CFD_strainField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.strainField)
        self.labels = ["mag"]
        self.nperbin = 1

    def read(self,startrec,endrec, binlimits=None,**kwargs):
        dudr = self.strainField.read(startrec, endrec, 
                                      binlimits=None)

        vortdata = np.empty([dudr.shape[0],dudr.shape[1],
                             dudr.shape[2],dudr.shape[3],self.nperbin])
        vortdata[:,:,:,:,0] = ( np.power(dudr[:,:,:,:,0],2.)
                               +np.power(dudr[:,:,:,:,1],2.)
                               +np.power(dudr[:,:,:,:,2],2.))


        if (binlimits):

            # Defaults
            lower = [0]*3
            upper = [i for i in vortdata.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            vortdata = vortdata[lower[0]:upper[0],
                                lower[1]:upper[1],
                                lower[2]:upper[2], :, :]

        return  vortdata


