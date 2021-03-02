#! /usr/bin/env python
import numpy as np
import os

from .rawdata import RawData
from .pplexceptions import DataNotAvailable

class PsiBoil_RawData(RawData):
    
    def __init__(self, fdir):
        self.fdir = fdir
        self.subdomlist = self.get_subdomlist()
        self.grid = self.get_grid()
        self.npercell = self.get_npercell()
        self.maxrec = len(self.subdomlist)-1 # count from 0
        self.header = None

    def get_grid(self):
        try:
            fobj = "PUTPSIBOILFILETYPEHERE"
        except IOError:
            raise DataNotAvailable

        #Read Header data first then remaining file
        with open(self.fdir+self.subdomlist[0],'r') as f:
            imin, imax, jmin, jmax, kmin, kmax, nx, ny, nz = np.fromfile(f,dtype="i4",count=9)
            data = np.fromfile(f,dtype="f8",count=(nx+ny+nz))

        # Number of grid points in main code
        self.nx = nx
        self.ny = ny
        self.nz = nz

        # Number of cell-centered values written to files
        self.nrx = self.nx
        self.nry = self.ny
        self.nrz = self.nz

        #Grid data
        gridx = data[0:nx]
        gridy = data[nx:nx+ny]
        gridz = data[nx+ny:nx+ny+nz]
        grid = [gridx,gridy,gridz]

        # Domain lengths
        self.xL = np.max(gridx)
        self.yL = np.max(gridy)
        self.zL = np.max(gridz)

        # Grid spacing
        self.dx = np.diff(gridx)
        self.dy = np.diff(gridy)
        self.dz = np.diff(gridz)

        return grid 

    def get_subdomlist(self):

        def get_int(name):
            string = name.replace('.bin','')
            integer = name.split('_')[-1]

            return int(integer)

        subdoms = []
        for filename in os.listdir(self.fdir):
            if (filename.find('.bin') != -1):
                subdoms.append(filename)

        if (len(subdoms) == 0):
            raise DataNotAvailable

        return sorted(subdoms,key=get_int)       

    def get_npercell(self):
        dprealbytes = 8 # 8 for dp float
        ngridpoints = self.nrx * self.nry * self.nrz
        filepath = self.fdir + self.subdomlist[0]
        filesize = os.path.getsize(filepath)
        npercell = filesize / (dprealbytes*ngridpoints) 
        return npercell

    def read(self,startrec,endrec,binlimits=None,verbose=False,**kwargs):

        nrecs = endrec - startrec + 1
        # Efficient memory allocation
        subdata = np.empty((self.nrx,self.nry,self.nrz,nrecs,self.npercell))

        # Loop through files and insert data
        for plusrec in range(0,nrecs):

            fpath = self.fdir + self.get_subdomlist().pop(startrec+plusrec)
            with open(fpath,'rb') as fobj:
                data = np.fromfile(fobj,dtype='d')
                # zxy ordered in file
                try:
                    data = np.reshape(data,[self.nrz,self.nrx,self.nry,self.npercell],
                                      order='F')
                except ValueError:
                    print('Data in CFD file seems wrong -- maybe it includes halos?'
                          'Attempting to correct')
                    if (data.shape[0] > self.nrz*self.nrx*self.nry*self.npercell):
                        data = np.reshape(data,[self.nrz+1,self.nrx+1,self.nry,self.npercell],
                                          order='F')
                        data = data[:-1,:-1,:,:]
                    else:
                        data = np.reshape(data,[self.nrz-1,self.nrx-1,self.nry,self.npercell],
                                          order='F')
                        data = data[:-1,:-1,:,:]

                # change to xyz ordering
                data = np.transpose(data,(1,2,0,3))
                # insert into array
                subdata[:,:,:,plusrec,:] = data 

        # If bin limits are specified, return only those within range
        if (binlimits):

            if (verbose):
                print(('subdata.shape = {0:s}'.format(str(subdata.shape))))
                print(('Extracting bins {0:s}'.format(str(binlimits))))

            # Defaults
            lower = [0]*3
            upper = [i for i in subdata.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            subdata = subdata[lower[0]:upper[0],
                              lower[1]:upper[1],
                              lower[2]:upper[2], :, :]
         
        return subdata
