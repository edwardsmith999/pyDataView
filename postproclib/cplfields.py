#! /usr/bin/env python
import numpy as np
try:
    import skimage.transform as skit
    skit_imported=True
except:
    skit_imported=False
    skit_imported_fail_message = (
              'You have not been able to import the skimage.transform '
            + '\npackage, which is required for MDField resampling. Try '
            + '\nCPLField.?_both instead, where ? is profile/contour/etc, '
            + '\nin which no resampling is performed.') 

from . import cfdfields
from . import mdfields
from . import lammpsfields
from . import serial_cfdfields
from . import openfoamfields
from .headerdata import HeaderData
from .field import Field

class CPLField(Field):
    
    def __init__(self,fdir,cpldir='cpl/',
                           mddir='md/results/',
                           cfddir='cfd/',
                           **kwargs):
        self.fdir = fdir
        self.cpldir = cpldir
        self.mddir = mddir
        self.cfddir = cfddir
        self.header = HeaderData(open(fdir+cpldir+'coupler_header')) 
        self.md_field = self.MDFieldType(fdir+mddir, **kwargs)
        try:
            self.cfd_field = self.CFDFieldType(fdir+cfddir, parallel_run=True)
        except TypeError:
            self.cfd_field = self.CFDFieldType(fdir+cfddir)
        self.cfd_halos = self.cfd_field.nhalos
        self.olap_cells = np.array(
            [int(self.header.icmax_olap) - int(self.header.icmin_olap) + 1,
             int(self.header.jcmax_olap) - int(self.header.jcmin_olap) + 1,
             int(self.header.kcmax_olap) - int(self.header.kcmin_olap) + 1 ])
        self.cfd_dxyz=np.empty(3)
        self.CFD_2d = [False, False, False]
        for i in range(3):
            if self.cfd_field.grid[i].shape[0] > 1:
                self.cfd_dxyz[i] = np.array(self.cfd_field.grid[i][1] - 
                                            self.cfd_field.grid[i][0]  )
            else:
                self.cfd_dxyz[i] = self.cfd_field.Raw.xyzL[i]
                self.CFD_2d[i] = True

        self.density_cfd = float(self.header.density_cfd)
        self.cpl_dxyz = np.copy(self.cfd_dxyz)

        self.md_grid, self.cfd_grid = self.get_grids()

        md_dx, md_xL = self.get_d_and_L(self.md_grid[0])
        md_dy, md_yL = self.get_d_and_L(self.md_grid[1])
        md_dz, md_zL = self.get_d_and_L(self.md_grid[2])
        self.md_dxyz = [md_dx, md_dy, md_dz]
        self.md_xyzL = [md_xL, md_yL, md_zL]
        #self.md_xyzL = np.array([float(self.md_field.header.globaldomain1),
        #                         float(self.md_field.header.globaldomain2),
        #                         float(self.md_field.header.globaldomain3)])

        self.cfd_cells = np.array([int(len(self.cfd_field.grid[i])) 
                                  for i in range(3)])
        self.md_cells = np.array([int(len(self.md_field.grid[i])) 
                                 for i in range(3)])
        self.md_cfdcells = np.rint(np.divide(self.md_xyzL,
                                             self.cfd_dxyz)).astype(int)

        if any(self.md_cfdcells == 0):
            Errorstr = ("CPLField Error - md_cfdcells is zero \n" + 
                       "MD domain= " + str(self.md_xyzL) + " \n" +
                       "CFD cell= " + str(self.cfd_dxyz))
            raise Exception(Errorstr)

        self.cpl_cells = (self.md_cfdcells + self.cfd_cells 
                        - self.olap_cells  - self.cfd_halos)
        #self.md_grid, self.cfd_grid = self.get_grids()
        self.maxrec = self.md_field.maxrec 
        self.grid = self.get_cpl_grid()

        self.labels = self.md_field.labels
        self.axislabels = self.md_field.axislabels
        self.Raw = self.md_field.Raw
        self.plotfreq = self.md_field.plotfreq

    def get_grids(self):

        md_grid = self.md_field.grid
        cfd_grid = self.cfd_field.grid

        # Add MD domain (minus olap size) to CFD y grid
        #md_yL = float(self.md_field.header.globaldomain2)
        md_dy, md_yL = self.get_d_and_L(md_grid[1])
        olap_yL = self.olap_cells[1] * self.cfd_dxyz[1]
        cfd_grid[1] += md_yL - olap_yL
        #Adjust md_grid to zero origin
        md_grid[1] = md_grid[1] - md_grid[1][0] + md_dy/2.

        return md_grid, cfd_grid  

    def get_d_and_L(self, grid1):
        """
            Get grid domain and spacing assuming list of cell-centered nodes
        """ 
        d = grid1[1] - grid1[0]
        L = grid1[-1] - grid1[0] + d
        return d, L 

    def get_cpl_grid(self):
        gridx = (np.arange(0,self.cpl_cells[0])+0.5)*self.cpl_dxyz[0]
        gridy = (np.arange(0,self.cpl_cells[1])+0.5)*self.cpl_dxyz[1]
        gridz = (np.arange(0,self.cpl_cells[2])+0.5)*self.cpl_dxyz[2]
        grid = [gridx, gridy, gridz]
        return grid
        
    def read(self,startrec,endrec,binlimits=None,**kwargs):
        
        if (not skit_imported):
            quit(skit_imported_fail_message)

        md_data = self.md_field.read(startrec,endrec)
        cfd_data = self.cfd_field.read(startrec,endrec)

        ndims =  min(self.md_field.nperbin,
                     self.cfd_field.nperbin) #md_data.shape[-1]
        nrecs = endrec - startrec + 1

        md_coarse = np.empty([self.md_cfdcells[0],self.md_cfdcells[1],
                              self.md_cfdcells[2],nrecs,ndims])
        zoom = np.divide(self.md_cfdcells.astype(float),
                         self.md_cells.astype(float))

        #import matplotlib.pyplot as plt
        dims = self.CFD_2d.count(False)
        for rec in range(nrecs):
            for comp in range(ndims):
                md_coarse[:,:,:,rec,comp]=skit.resize(md_data[:,:,:,rec,comp],
                                                             self.md_cfdcells)
                dim = comp % dims 
                if self.CFD_2d[dim]:
                    temp = np.expand_dims(cfd_data, axis=comp)
                    temp = np.lib.pad(temp,md_coarse.shape[comp],'mean')

        jstart = self.olap_cells[1] - 1 + self.cfd_halos[1]
        cfd_data = cfd_data[:,jstart:,:,:,:]
        md_coarse = md_coarse[:,:-1,:,:,:]
        #jstart = self.olap_cells[1] + self.cfd_halos[1]
        #cfd_data = cfd_data[:,jstart:,:,:,:]

        cpl_data = np.concatenate((md_coarse,cfd_data),axis=1)
        
        if (binlimits):

            # Defaults
            lower = [0]*3
            upper = [i for i in cpl_data.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            cpl_data = cpl_data[lower[0]:upper[0],
                                lower[1]:upper[1],
                                lower[2]:upper[2]]
            
        return cpl_data
    
    def profile_both(self,axis,startrec=0,endrec=None,**kwargs):
         
        avgaxes = [0,1,2,3]
        avgaxes.remove(axis)
        avgaxes = tuple(avgaxes)

        if (endrec==None): 
            endrec = self.maxrec

        md_data = self.md_field.averaged_data(startrec,endrec,avgaxes=avgaxes,
                                              **kwargs)
        cfd_data = self.cfd_field.averaged_data(startrec,endrec,
                                                avgaxes=avgaxes, **kwargs)
        return self.md_grid[axis], md_data, self.cfd_grid[axis], cfd_data 

    def profile_both_cnstinfo(self, axis, startrec=0, endrec=None, **kwargs):

        md_ax, md_data, cfd_ax, cfd_data = self.profile_both(axis,
                                                startrec=startrec,
                                                endrec=endrec, **kwargs)

        dx = cfd_ax[1] - cfd_ax[0]
        uppercellfaces = cfd_ax + 0.5*dx
        lowercellfaces = cfd_ax - 0.5*dx

        # -1 to compensate Fortran indexing
        if (axis == 0):
            lowercnstcell = int(self.header.icmin_cnst) - 1 + self.cfd_halos[0] 
            uppercnstcell = int(self.header.icmax_cnst) - 1 + self.cfd_halos[0] 
        elif (axis == 1):
            lowercnstcell = int(self.header.jcmin_cnst) - 1 + self.cfd_halos[1] 
            uppercnstcell = int(self.header.jcmax_cnst) - 1 + self.cfd_halos[1]
        elif (axis == 2):
            lowercnstcell = int(self.header.kcmin_cnst) - 1 + self.cfd_halos[2] 
            uppercnstcell = int(self.header.kcmax_cnst) - 1 + self.cfd_halos[2] 
        else:
            raise

        # Constrained MD cells
        cnst_md = np.logical_and(md_ax>lowercellfaces[lowercnstcell],
                                 md_ax<uppercellfaces[uppercnstcell])
        md_ax_cnst = md_ax[cnst_md]
        md_data_cnst = md_data[cnst_md]

        # CFD boundary condition only output for y axis
        if (axis == 1):
            cfd_ax_bc = np.array([cfd_ax[0], cfd_ax[-1]])
            cfd_data_bc = np.array([ cfd_data[0,:], cfd_data[-1,:] ])
        else:
            cfd_ax_bc = np.array([None, None])
            cfd_data_bc = np.array([ 
                                     [None]*cfd_data.shape[1], 
                                     [None]*cfd_data.shape[1] 
                                   ])

        return (md_ax, md_data, cfd_ax, cfd_data, md_ax_cnst, md_data_cnst, 
               cfd_ax_bc, cfd_data_bc)

class CPL_vField(CPLField):

    nperbin = 3

    def __init__(self, fdir, MDFieldType=mdfields.MD_vField, 
                 CFDFieldType=cfdfields.CFD_vField, cpldir='cpl/', 
                 mddir='md/results/', cfddir='cfd/', **kwargs):

        self.MDFieldType = MDFieldType
        self.CFDFieldType = CFDFieldType
        CPLField.__init__(self, fdir, cpldir=cpldir, mddir=mddir,
                          cfddir=cfddir, **kwargs)

class CPL_momField(CPLField):
    nperbin = 3

    def __init__(self, fdir, MDFieldType=mdfields.MD_vField, 
                 CFDFieldType=cfdfields.CFD_vField, cpldir='cpl/', 
                 mddir='md/results/', cfddir='cfd/', **kwargs):

        self.MDFieldType = MDFieldType
        self.CFDFieldType = CFDFieldType
        CPLField.__init__(self,fdir,cpldir=cpldir, mddir=mddir,
                          cfddir=cfddir, **kwargs)

class CPL_stressField(CPLField):

    nperbin = 9

    def __init__(self, fdir, MDFieldType=mdfields.MD_stressField, 
                 CFDFieldType=cfdfields.CFD_mugradvField, cpldir='cpl/', 
                 mddir='md/results/', cfddir='cfd/', **kwargs):

        self.MDFieldType = MDFieldType
        self.CFDFieldType = CFDFieldType
        CPLField.__init__(self, fdir, cpldir=cpldir, mddir=mddir,
                          cfddir=cfddir, **kwargs)
        self.cfd_field.set_rho(self.density_cfd)

#class CPL_Serial_CFD_vField(CPLField):
#    nperbin = 3
#    MDFieldType = mdfields.MD_vField 
#    CFDFieldType = serial_cfdfields.Serial_CFD_vField
#
#    def __init__(self, fdir):
#        CPLField.__init__(self,fdir,cfddir='couette_serial/results/')
#

#class CPL_Serial_CFD_stressField(CPLField):
#    nperbin = 18
#    MDFieldType = mdfields.MD_pfluxField
#    nperbin = 4
#    CFDFieldType = serial_cfdfields.Serial_CFD_StressField
#
#    def __init__(self, fdir):
#        CPLField.__init__(self,fdir,cfddir='couette_serial/results/',fname='psurface')

