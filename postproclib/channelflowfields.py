#! /usr/bin/env python
import numpy as np
from field import Field
from channelflowrawdata import Channelflow_RawData

# ============================================================================
# CFDField base class

class ChannelflowField(Field):

    def __init__(self,fdir):
        Raw = Channelflow_RawData(fdir)
        Field.__init__(self,Raw)
        self.axislabels = ['x','y','z']

# ============================================================================
# CFDField derived classes, but calculated by the main code
class Channelflow_vField(ChannelflowField):

    nperbin = 3 
    labels = ['u','v','w']

    def read(self,startrec,endrec,**kwargs):

        v = ChannelflowField.read(self,startrec,endrec,**kwargs)
        return v 

# ============================================================================
# Complex fields that require extra calculations. 

class Channelflow_complexField(ChannelflowField):
   
    def inherit_parameters(self, subfieldobj):
        self.header = subfieldobj.Raw.header
        self.nperbin = subfieldobj.nperbin
        self.cpol_bins = False
        self.plotfreq = subfieldobj.Raw.plotfreq
        self.axislabels = subfieldobj.axislabels
        self.labels = subfieldobj.labels


class Channelflow_strainField(Channelflow_complexField,Channelflow_vField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = Channelflow_vField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.labels = ["dudx","dudy","dudz",
                       "dvdx","dvdy","dvdz",
                       "dwdx","dwdy","dwdz"]
        self.nperbin = 9

    def read(self,startrec,endrec, binlimits=None,**kwargs):
        vdata = self.vField.read(startrec, endrec, 
                                 binlimits=None)

        grid = self.vField.Raw.grid
        x, y, z = grid
        dx = np.gradient(x)
        dy = np.gradient(y)
        dz = np.gradient(z)
        dX,dY,dZ = np.meshgrid(dx,dy,dz,indexing='ij')

        straindata = self.grad(vdata,dX,dY,dZ)

#        straindata = np.zeros((vdata.shape[0],vdata.shape[1],vdata.shape[2],vdata.shape[3],9))
#        print(vdata.shape)
#        for i in range(1,vdata.shape[0]):
#            for j in range(1,vdata.shape[1]):
#                for k in range(1,vdata.shape[2]):
#                    straindata[i,j,k,:,0] = (vdata[i+1,j,k,:,0]-vdata[i-1,j,k,:,0])/(2.*(x[i+1]-x[i-1]))
#                    straindata[i,j,k,:,1] = (vdata[i+1,j,k,:,1]-vdata[i-1,j,k,:,1])/(2.*(x[i+1]-x[i-1]))
#                    straindata[i,j,k,:,2] = (vdata[i+1,j,k,:,2]-vdata[i-1,j,k,:,2])/(2.*(x[i+1]-x[i-1]))

#                    straindata[i,j,k,:,3] = (vdata[i,j+1,k,:,0]-vdata[i,j-1,k,:,0])/(2.*(y[j+1]-y[j-1]))
#                    straindata[i,j,k,:,4] = (vdata[i,j+1,k,:,1]-vdata[i,j-1,k,:,1])/(2.*(y[j+1]-y[j-1]))
#                    straindata[i,j,k,:,5] = (vdata[i,j+1,k,:,2]-vdata[i,j-1,k,:,2])/(2.*(y[j+1]-y[j-1]))

#                    straindata[i,j,k,:,6] = (vdata[i,j,k+1,:,0]-vdata[i,j,k-1,:,0])/(2.*(z[k+1]-z[k-1]))
#                    straindata[i,j,k,:,7] = (vdata[i,j,k+1,:,1]-vdata[i,j,k-1,:,1])/(2.*(z[k+1]-z[k-1]))
#                    straindata[i,j,k,:,8] = (vdata[i,j,k+1,:,2]-vdata[i,j,k-1,:,2])/(2.*(z[k+1]-z[k-1]))

#                    print(i,j,k,straindata[i,j,k,0,:])

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

class Channelflow_uuField(Channelflow_complexField):

    def __init__(self, fdir):

        # Get mean velocity and density field
        self.fdir = fdir
        self.vField = Channelflow_vField(fdir)
        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.vField)
        self.labels = ['uu','uv','uw',
                       'vu','vv','vw',
                       'wu','wv','ww']
        self.nperbin = 9

    def read(self,startrec,endrec,**kwargs):
        vdata = self.vField.read(startrec,endrec,**kwargs)

        # Find outer product of v*v and reshape to 1x9 rather than 3x3
        nrecs = endrec-startrec+1
        rhovvdata = np.einsum('abcdj,abcdk->abcdjk',vdata,vdata)
        vvshapelist = list(rhovvdata.shape)
        newshape = tuple(vvshapelist[0:4]+[self.nperbin])
        rhovvdata = np.reshape(rhovvdata,newshape)

        return rhovvdata 


class Channelflow_vortField(Channelflow_complexField,Channelflow_vField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = Channelflow_vField(fdir)
        self.strainField = Channelflow_strainField(fdir)

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


class Channelflow_dissipField(Channelflow_complexField,Channelflow_vField):

    def __init__(self,fdir,rectype='bins'):
        self.vField = Channelflow_vField(fdir)
        self.strainField = Channelflow_strainField(fdir)

        Field.__init__(self,self.vField.Raw)
        self.inherit_parameters(self.strainField)
        self.labels = ["mag"]
        self.nperbin = 1

    def read(self,startrec,endrec, binlimits=None,**kwargs):
        dudr = self.strainField.read(startrec, endrec, 
                                      binlimits=None)

        dissipdata = np.empty([dudr.shape[0],dudr.shape[1],
                               dudr.shape[2],dudr.shape[3],self.nperbin])

        #From Viswanath 2006 D = \int_V |del u|^2 + |del v|^2 + |del w|^2 dV
#        dissipdata[:,:,:,:,0] = (  np.power(dudr[:,:,:,:,0] 
#                                          + dudr[:,:,:,:,1] 
#                                          + dudr[:,:,:,:,2],2)
#                                 + np.power(dudr[:,:,:,:,3] 
#                                          + dudr[:,:,:,:,4] 
#                                          + dudr[:,:,:,:,5],2)
#                                 + np.power(dudr[:,:,:,:,6] 
#                                          + dudr[:,:,:,:,7] 
#                                          + dudr[:,:,:,:,8],2))

        dissipdata[:,:,:,:,0] = ( np.power(dudr[:,:,:,:,0],2.) +
                                  np.power(dudr[:,:,:,:,4],2.) +
                                  np.power(dudr[:,:,:,:,8],2.) +
                                  np.power(dudr[:,:,:,:,1],2.) +
                                  np.power(dudr[:,:,:,:,2],2.) +
                                  np.power(dudr[:,:,:,:,3],2.) +
                                  np.power(dudr[:,:,:,:,5],2.) +
                                  np.power(dudr[:,:,:,:,6],2.) +
                                  np.power(dudr[:,:,:,:,7],2.)   )


        #print('dissip data = ',dudr[3,100,3,0,:],dissipdata[3,100,3,0,0])

        if (binlimits):

            # Defaults
            lower = [0]*3
            upper = [i for i in dissipdata.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            dissipdata = dissipdata[lower[0]:upper[0],
                                    lower[1]:upper[1],
                                    lower[2]:upper[2], :, :]

        return  dissipdata

