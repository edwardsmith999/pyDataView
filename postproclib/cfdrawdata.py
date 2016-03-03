#! /usr/bin/env python
import numpy as np
import os

from rawdata import RawData
from pplexceptions import DataNotAvailable

class CFD_RawData(RawData):
    
    def __init__(self,fdir):
        self.fdir = fdir
        self.grid = self.get_grid()
        self.subdomlist = self.get_subdomlist()
        self.npercell = self.get_npercell()
        self.maxrec = len(self.subdomlist)-1 # count from 0
        self.Re, self.nu = self.get_couette_params()
        self.header = None

    def get_couette_params(self):

        def extract_param(string):
            with open(self.fdir+'input','r') as fobj:
                param = float(fobj.read().split(string)[0].split()[-1])
            return param

        Re = extract_param('Re')
        #Umax = extract_param('uwall_t')
        #L = 1.0
        #nu = Umax*L/Re
        nu = 1.0/Re
        return Re, nu

    def get_grid(self):
        try:
            fobj = open(self.fdir+'report','r')
        except IOError:
            raise DataNotAvailable
        report = fobj.readlines()[3:6] # Lines with info in
        for line in report:
            linepairs = line.split('|')
            for pair in linepairs:
                varname = pair.split()[0]
                varval  = pair.split()[1]
                vars(self)[varname] = varval    
        # Number of grid points in main code
        self.nx = int(self.nx)
        self.ny = int(self.ny)
        self.nz = int(self.nz)
        # Number of cell-centered values written to files
        # -1 for cell centers rather than grid points
        # -2 for not writing halos (except in y-direction)
        # Therefore -3 in x and z, -1 in y
        self.nrx = int(self.nx)-3 # number of subdom grid records in x
        self.nry = int(self.ny)-3+2 # +2 halos
        self.nrz = int(self.nz)-3
        # Domain lengths
        self.xL = float(self.xL)
        self.yL = float(self.yL)
        self.zL = float(self.zL)
        # Grid spacing
        self.dx = self.xL/float(self.nx-3)
        self.dy = self.yL/float(self.ny-3)
        self.dz = self.zL/float(self.nz-3)
        # Linspaces of cell centers, accounting for halos written in y
        gridx = np.linspace( self.dx/2., self.xL -self.dx/2., num=self.nrx)
        gridy = np.linspace(-self.dy/2., self.yL +self.dy/2., num=self.nry)
        gridz = np.linspace( self.dz/2., self.zL -self.dz/2., num=self.nrz)
        grid = [gridx,gridy,gridz]

        return grid 

    def get_subdomlist(self):

        def get_int(name):
            string, integer = name.split('.')
            return int(integer)

        subdoms = []
        for filename in os.listdir(self.fdir):
            if (filename.find('SubDom') != -1):
                subdoms.append(filename)

        if (len(subdoms) == 0):
            raise DataNotAvailable

        subdoms = sorted(subdoms,key=get_int)
        
        # CFD writes a record at the beginning, so remove it
        subdoms = subdoms[1:]
        return subdoms

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
                    print('Data in CFD file seems wrong -- maybe it includes halos? \n'
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
                print('subdata.shape = {0:s}'.format(str(subdata.shape)))
                print('Extracting bins {0:s}'.format(str(binlimits)))

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
