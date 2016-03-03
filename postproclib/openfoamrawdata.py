#! /usr/bin/env python
import numpy as np
import os

from rawdata import RawData
from pplexceptions import DataNotAvailable

class OpenFOAM_RawData(RawData):
    
    def __init__(self, fdir, fname):

        if (fdir[-1] != '/'): fdir += '/'
        self.fdir = fdir
        self.grid = self.get_grid()
        self.reclist = self.get_reclist()
        self.maxrec = len(self.reclist) - 1 # count from 0
        self.fname = fname
        self.npercell = self.get_npercell()
        self.nu = self.get_nu()
        self.header = None

    def get_nu(self):

        # Read constant transport properties file 
        fpath = self.fdir+'constant/transportProperties'
        with open(fpath, 'r') as f:
            while True:
                line = f.readline()
                if (line[0:2] == 'nu'):
                    break
            nu = float(line.split(']')[-1].split(';')[0]) 
        
        return nu
    
    def get_npercell(self):

        # Read first record (reclist[0]) as example 
        fpath = self.fdir+self.reclist[0]+self.fname 
        with open(fpath, 'r') as f:
            while True:
                line = f.readline()
                if ('(' in line and ')' in line):
                    break
            npercell = len(line.split())

        return npercell
            

    def reshape_list_to_grid(self, inputlist, nperpoint):
        # Lists from OpenFOAM seem to be written in Fortran order, for some
        # reason
        array = np.reshape(
                           inputlist, 
                           (self.ngx, self.ngy, self.ngz, nperpoint), 
                           order='F'
                          ) 
        return array

    def reshape_list_to_cells(self, inputlist, npercell):
        # Lists from OpenFOAM seem to be written in Fortran order, for some
        # reason
        array = np.reshape(
                           inputlist, 
                           (self.ncx, self.ncy, self.ncz, npercell), 
                           order='F'
                          ) 
        return array

    def read_list(self, fobj):

        flist = []
        for line in fobj:
            if line[0] == '(' and ')' in line:
                values = line.split('(')[-1].split(')')[0].split()
                flist.append([float(i) for i in values])
        return flist

    def read_list_named_entry(self, fobj, entryname):

        def read_list_from_here(fobj):

            nitems = int(fobj.next())
            checkopenbracket = fobj.next()
            if (checkopenbracket[0] != '('):
                raise 

            herelist = []
            for lineno in range(nitems):
                line = fobj.next()
                if line[0] == '(' and ')' in line:
                    values = line.split('(')[-1].split(')')[0].split()
                    herelist.append([float(i) for i in values])

            checkclosebracket = fobj.next()
            if (checkclosebracket[0] != ')'):
                raise
    
            return herelist
            
        for line in fobj:
            if (entryname in line):
                flist = read_list_from_here(fobj)

        return flist
    
    def get_grid(self):

        """
            OpenFOAM writes data at cell centers
        """

        # Try to get grid shape (linear)
        try:
            fobj = open(self.fdir+'constant/polyMesh/blockMeshDict','r')
        except IOError:
            raise DataNotAvailable

        while True:
            line = fobj.readline()
            if line[0:6] == 'blocks':
                fobj.readline()
                hexentry = fobj.readline()
                nxyz = hexentry.split('(')[2].split(')')[0].split()
                break

        # Number of grid points is 1 more than number of cells
        self.ngx = int(nxyz[0]) + 1 
        self.ngy = int(nxyz[1]) + 1
        self.ngz = int(nxyz[2]) + 1
        # Number of cells of openfoam output 
        self.ncx = self.ngx - 1
        self.ncy = self.ngy - 1
        self.ncz = self.ngz - 1

        # Read list of points and reshape to assumed linear grid
        try:
            fobj = open(self.fdir+'constant/polyMesh/points','r')
        except IOError:
            raise DataNotAvailable

        # Read openfoam list of points
        pointslist = self.read_list(fobj)
        # Reshape to structured grid, 3 values (x,y,z pos) for each point 
        points = self.reshape_list_to_grid(np.array(pointslist), 3)

        # Extract useful quantities from structured grid
        dummy = 0; x = 0; y = 1; z = 2 
        self.dx = points[1,dummy,dummy,x] - points[0,dummy,dummy,x]
        self.dy = points[dummy,1,dummy,y] - points[dummy,0,dummy,y]
        self.dz = points[dummy,dummy,1,z] - points[dummy,dummy,0,z]
        self.xL = points[-1,dummy,dummy,x] - points[0,dummy,dummy,x]
        self.yL = points[dummy,-1,dummy,y] - points[dummy,0,dummy,y]
        self.zL = points[dummy,dummy,-1,z] - points[dummy,dummy,0,z]

        # Return list of cell-centre locations in each direction
        gridx = np.linspace(self.dx/2., self.xL - self.dx/2., num=self.ncx)
        gridy = np.linspace(self.dy/2., self.yL - self.dy/2., num=self.ncy)
        gridz = np.linspace(self.dz/2., self.zL - self.dz/2., num=self.ncz)
        
        grid = [gridx,gridy,gridz]

        return grid 

    def get_reclist(self):

        def get_float(name):
            return float(name)

        records = []
        for filename in os.listdir(self.fdir):
            try:
                rectime = float(filename)
                records.append(filename)
            except ValueError:
                print('Ignoring folder '+self.fdir+filename)
       
        records = sorted(records, key=get_float)
        # Ignore initial field stored in folder "0" 
        return [rectime+'/' for rectime in records[1:]]

    def read(self, startrec, endrec, binlimits=None, verbose=False, **kwargs):

        nrecs = endrec - startrec + 1

        # Allocate storage (despite ascii read!)
        odata = np.empty((self.ncx,self.ncy,self.ncz,nrecs,self.npercell))

        # Loop through files and insert data
        for plusrec in range(0,nrecs):

            fpath = self.fdir + self.reclist[startrec+plusrec] + self.fname
            with open(fpath,'r') as fobj:
                vlist = self.read_list_named_entry(fobj, 'internalField')
                vtemp = self.reshape_list_to_cells(vlist, self.npercell)

            odata[:,:,:,plusrec,:] = vtemp 
                
        # If bin limits are specified, return only those within range
        if (binlimits):

            if (verbose):
                print('odata.shape = {0:s}'.format(str(odata.shape)))
                print('Extracting bins {0:s}'.format(str(binlimits)))

            # Defaults
            lower = [0]*3
            upper = [i for i in odata.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            odata = odata[lower[0]:upper[0],
                          lower[1]:upper[1],
                          lower[2]:upper[2], :, :]
         
        return odata
