#! /usr/bin/env python
import numpy as np

from .field import Field
from .openfoamrawdata import OpenFOAM_RawData

# ============================================================================
# OpenFOAMField base class

class OpenFOAMField(Field):

    nhalos = [0, 0, 0]

    def __init__(self, fdir, fname, parallel_run=None):
        Raw = OpenFOAM_RawData(fdir, fname,
                               self.nperbin,
                               parallel_run=parallel_run)
        Field.__init__(self, Raw)
        self.axislabels = ['x','y','z']
        self.plotfreq = self.Raw.Nave

class OpenFOAMdummyField(OpenFOAMField):

    """
        Dummy field object
    """

    dtype = 'd'
    nperbin = 1

    def __init__(self, fdir, parallel_run=None):
        
        self.fname = "dummy"
        self.labels = ['scalar']
        OpenFOAMField.__init__(self, fdir, self.fname)
        self.labels = [""]
        self.nperbin = 1
        self.plotfreq = 1

# ============================================================================
# OpenFOAMField derived classes scalar, vector and tensor fields
class OpenFOAM_ScalarField(OpenFOAMField):

    nperbin = 1

    def __init__(self, fdir, fname, parallel_run=None):
        OpenFOAMField.__init__(self, fdir, fname, parallel_run)
        self.fname = fname
        self.labels = ['scalar']

class OpenFOAM_VectorField(OpenFOAMField):

    nperbin = 3 

    def __init__(self, fdir, fname, parallel_run=None):
        OpenFOAMField.__init__(self, fdir, fname, parallel_run)
        self.fname = fname
        self.labels = ['x', 'y', 'z']

class OpenFOAM_SymmTensorField(OpenFOAMField):

    nperbin = 6

    def __init__(self, fdir, fname, parallel_run=None):
        OpenFOAMField.__init__(self, fdir, fname, parallel_run)
        self.fname = fname
        self.labels = ['xx', 'xy', 'xz', "yy", "yz", "zz"]


#class OpenFOAM_surfaceScalarField(OpenFOAMField):

#    The total size is 3 x 7 x 8 x 8, not clear how we parse this...

#    nperbin = 6

#    def __init__(self, fdir, fname, parallel_run=None):
#        OpenFOAMField.__init__(self, fdir, fname, parallel_run)
#        self.fname = fname
#        self.labels = ["xbottom","ybottom","zbottom",
#                        "xtop","ytop","ztop"]

# ============================================================================
# OpenFOAMField derived classes, but calculated by the main code
class OpenFOAM_vField(OpenFOAMField):

    nperbin = 3 
    fname = 'U'

    def __init__(self, fdir, parallel_run=None):
        OpenFOAMField.__init__(self, fdir, self.fname, parallel_run)
        self.labels = ['u', 'v', 'w']

# ============================================================================
# OpenFOAMField derived classes, but calculated by the main code
class OpenFOAM_momField(OpenFOAMField):

    nperbin = 3 
    fname = 'U'

    def __init__(self, fdir, parallel_run=None):
        OpenFOAMField.__init__(self, fdir, self.fname, parallel_run)
        self.labels = ['u', 'v', 'w']


    def read(self, startrec, endrec, binlimits=None, **kwargs):
        U = OpenFOAMField.read(self, startrec, endrec, **kwargs)
        print("WARNING FROM OpenFOAM_momField, NEEDS RHO, ASSUMING 0.8")
        return U*0.8



class OpenFOAM_FField(OpenFOAMField):

    nperbin = 3 
    fname = 'F'

    def __init__(self, fdir, parallel_run=None):
        OpenFOAMField.__init__(self, fdir, self.fname, parallel_run)
        self.labels = ['Fx', 'Fy', 'Fz']


class OpenFOAM_PField(OpenFOAMField):

    nperbin = 1
    fname = 'p' 

    def __init__(self, fdir, parallel_run=None):
        OpenFOAMField.__init__(self, fdir, self.fname, parallel_run)
        self.labels = ['p']


class OpenFOAM_epsField(OpenFOAMField):

    nperbin = 1
    fname = 'eps'

    def __init__(self, fdir, parallel_run=None):
        OpenFOAMField.__init__(self, fdir, self.fname, parallel_run)
        self.labels = ['eps']

#class OpenFOAM_StressField(OpenFOAMField):
#
#    nperbin = 9    
#    def __init__(self,fdir):
#        OpenFOAMField.__init__(self,fdir)
#        assert self.Raw.npercell > 4
#        x = self.axislabels[0]; y = self.axislabels[1]; z = self.axislabels[2]
#        self.labels = [x+x,x+y,x+z,
#                       y+x,y+y,y+z,
#                       z+x,z+y,z+z]
#
#    def read(self,startrec,endrec,binlimits=None,**kwargs):
#        subdata = OpenFOAMField.read(self,startrec,endrec,binlimits=binlimits,
#                                **kwargs) 
#        P = subdata[:,:,:,:,4:]
#        return P 


## =============================================================================
## Complex fields that require extra calculations. 
class OpenFOAM_complexField(OpenFOAMField):
    
    def inherit_parameters(self, subfieldobj):
        self.header = subfieldobj.Raw.header
        self.nperbin = subfieldobj.nperbin
        self.cpol_bins = False
        self.plotfreq = subfieldobj.plotfreq
        self.axislabels = subfieldobj.axislabels
        self.labels = subfieldobj.labels


class OpenFOAM_mugradvField(OpenFOAM_complexField):
  
    nperbin = 9
 
    def __init__(self, fdir):
        self.vField = OpenFOAM_vField(fdir)
        OpenFOAM_complexField.__init__(self, fdir, self.vField.fname)
        x = self.axislabels[0]; y = self.axislabels[1]; z = self.axislabels[2]
        self.labels = [x+x,x+y,x+z,
                       y+x,y+y,y+z,
                       z+x,z+y,z+z]
        self.rho = None

    def set_rho(self, rho):
        self.rho = rho
        
    def read(self, startrec, endrec, binlimits=None, **kwargs):

        if (self.rho == None):
            print(('OpenFOAM_mugradvField requires rho, set by ' +
                  'OpenFOAM_mugradvField.set_rho(rho).'))
 
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

#class OpenFOAM_strainField(OpenFOAM_complexField,OpenFOAM_vField):
#
#    def __init__(self,fdir,rectype='bins'):
#        self.vField = OpenFOAM_vField(fdir)
#
#        Field.__init__(self,self.vField.Raw)
#        self.inherit_parameters(self.vField)
#        self.labels = ["dudx","dudy","dudz",
#                       "dvdx","dvdy","dvdz",
#                       "dwdx","dwdy","dwdz"]
#        self.nperbin = 9
#
#    def read(self,startrec,endrec, binlimits=None,**kwargs):
#        vdata = self.vField.read(startrec, endrec, 
#                                 binlimits=None)
#
#        straindata = self.grad(vdata)
#
#        if (binlimits):
#
#            # Defaults
#            lower = [0]*3
#            upper = [i for i in straindata.shape] 
#    
#            for axis in range(3):
#                if (binlimits[axis] == None):
#                    continue
#                else:
#                    lower[axis] = binlimits[axis][0] 
#                    upper[axis] = binlimits[axis][1] 
#
#            straindata = straindata[lower[0]:upper[0],
#                                    lower[1]:upper[1],
#                                    lower[2]:upper[2], :, :]
#
#        return straindata
#
#
#class OpenFOAM_vortField(OpenFOAM_complexField,OpenFOAM_vField):
#
#    def __init__(self,fdir,rectype='bins'):
#        self.vField = OpenFOAM_vField(fdir)
#        self.strainField = OpenFOAM_strainField(fdir)
#
#        Field.__init__(self,self.vField.Raw)
#        self.inherit_parameters(self.strainField)
#        self.labels = ["x","y","z"]
#        self.nperbin = 3
#
#    def read(self,startrec,endrec, binlimits=None,**kwargs):
#        dudr = self.strainField.read(startrec, endrec, 
#                                      binlimits=None)
#
#        vortdata = np.empty([dudr.shape[0],dudr.shape[1],
#                             dudr.shape[2],dudr.shape[3],self.nperbin])
#        vortdata[:,:,:,:,0] = ( dudr[:,:,:,:,7]
#                               -dudr[:,:,:,:,5])
#        vortdata[:,:,:,:,1] = ( dudr[:,:,:,:,2]
#                               -dudr[:,:,:,:,6])
#        vortdata[:,:,:,:,2] = ( dudr[:,:,:,:,3]
#                               -dudr[:,:,:,:,1])
#
#        if (binlimits):
#
#            # Defaults
#            lower = [0]*3
#            upper = [i for i in vortdata.shape] 
#    
#            for axis in range(3):
#                if (binlimits[axis] == None):
#                    continue
#                else:
#                    lower[axis] = binlimits[axis][0] 
#                    upper[axis] = binlimits[axis][1] 
#
#            vortdata = vortdata[lower[0]:upper[0],
#                                lower[1]:upper[1],
#                                lower[2]:upper[2], :, :]
#
#        return  vortdata
#
#
#class OpenFOAM_dissipField(OpenFOAM_complexField,OpenFOAM_vField):
#
#    def __init__(self,fdir,rectype='bins'):
#        self.vField = OpenFOAM_vField(fdir)
#        self.strainField = OpenFOAM_strainField(fdir)
#
#        Field.__init__(self,self.vField.Raw)
#        self.inherit_parameters(self.strainField)
#        self.labels = ["mag"]
#        self.nperbin = 1
#
#    def read(self,startrec,endrec, binlimits=None,**kwargs):
#        dudr = self.strainField.read(startrec, endrec, 
#                                      binlimits=None)
#
#        vortdata = np.empty([dudr.shape[0],dudr.shape[1],
#                             dudr.shape[2],dudr.shape[3],self.nperbin])
#        vortdata[:,:,:,:,0] = ( np.power(dudr[:,:,:,:,0],2.)
#                               +np.power(dudr[:,:,:,:,1],2.)
#                               +np.power(dudr[:,:,:,:,2],2.))
#
#
#        if (binlimits):
#
#            # Defaults
#            lower = [0]*3
#            upper = [i for i in vortdata.shape] 
#    
#            for axis in range(3):
#                if (binlimits[axis] == None):
#                    continue
#                else:
#                    lower[axis] = binlimits[axis][0] 
#                    upper[axis] = binlimits[axis][1] 
#
#            vortdata = vortdata[lower[0]:upper[0],
#                                lower[1]:upper[1],
#                                lower[2]:upper[2], :, :]
#
#        return  vortdata
#
#
