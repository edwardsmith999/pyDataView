#! /usr/bin/env python
import numpy as np
import subprocess as sp
import os
import sys
try:
    import h5py
except:
    print("h5py package not avilable -- using ascii conversion")

from rawdata import RawData
from pplexceptions import DataNotAvailable

class Channelflow_RawData(RawData):
    
    def __init__(self,fdir):
        self.fdir = fdir
        self.get_channelflow_utils()
        self.subdomlist, self.plotfreq = self.get_subdomlist()
        self.npercell = 3
        self.header = None
        self.grid = self.get_gridtopology()
        self.maxrec = len(self.subdomlist)-1 # count from 0
        try:
            self.read_field = self.read_h5field
        except:
            self.read_field = self.asciiread_field

    def get_channelflow_utils(self):

        """
            Find dirctory of compiled code and
            save a range of routine used for postprocessing
        """

        # Routine for converting spectral flowfied (.h5 format) to spectral flowfield (.ff format)
        self.fieldconvert = self.__syslocate('fieldconvert')
        # Routine for converting spectral flowfied (.h5 format) to realspace ascii and geom (.asc and .geom format)
        self.ascii2field = self.__syslocate('ascii2field')
        # Routine to get field geometry from spectral flowfied (.h5 format)
        self.fieldprops = self.__syslocate('fieldprops')

    def __syslocate(self,name):
        locout = sp.check_output(['locate',str(name)])
        return locout.split('\n')[0]

    def get_grid(self):
        print("Call to get_grid are depreciated, please use get_gridtopology instead")
        return self.get_gridtopology()

    def get_gridtopology(self):
        """
            Get details for CFD grid from 1st subdomain
        """

        self.filename = self.fdir + self.subdomlist[0] 
        self.get_geom()

        # Number of grid points in main code
        self.nx = int(self.Nx)*2./3.
        self.ny = int(self.Ny)
        self.nz = int(self.Nz)*2./3.
        # Number of cell-centered values written to files
        # -1 for cell centers rather than grid points
        # -2 for not writing halos (except in y-direction)
        # Therefore -3 in x and z, -1 in y
        self.nrx = int(self.Nx)*2./3. 
        self.nry = int(self.Ny) #
        self.nrz = int(self.Nz)*2./3.
        # Domain lengths
        self.xL = float(self.Lx)
        self.yL = float(self.Ly)
        self.zL = float(self.Lz)
        # Grid spacing (n.b. average in y as stretched grid)
        self.dx = self.xL/float(self.nx)
        self.dy = self.yL/float(self.ny)
        self.dz = self.zL/float(self.nz)
        # Linspaces of cell centers, accounting for halos written in y
        gridx = np.linspace( self.dx/2., self.xL -self.dx/2., num=self.nrx)
        gridy = self.cosinegrid(a=self.dy/2., b=self.yL-self.dy/2., Npoints=self.nry)
        gridz = np.linspace( self.dz/2., self.zL -self.dz/2., num=self.nrz)

        grid = [gridx,gridy,gridz]

        return grid

    def get_geom(self):
        try:
            rawgeomdata = sp.check_output([self.fieldprops,'-g', self.filename])
        except OSError:
            raise

        # Split into list and keep only variables
        variables = [x for x in rawgeomdata.split('\n') if x.find('==') != -1]

        #Evaluate and store as class variables
        for x in variables:
            try:
                exec('self.'+ x.replace('==','=').strip(' '))
            except:
                print("Can't save" + ' self.'+ x.replace('==','=').strip(' '))


    def get_binvolumes(self,binlimits=None):
        print("Call to get_binvolumes are depreciated, please use get_binvolumes instead")
        return self.get_gridvolumes(binlimits)

    def get_gridvolumes(self,binlimits=None):

        binspaces = self.grid
    
        x, y, z = np.meshgrid(binspaces[0],binspaces[1],binspaces[2],
                              indexing='ij')

        dx = binspaces[0][1] - binspaces[0][0]
        dy = binspaces[1][1] - binspaces[1][0]
        dz = binspaces[2][1] - binspaces[2][0]

        gridvolumes = np.ones(x.shape)*dx*dy*dz

        # If bin limits are specified, return only those within range
        if (binlimits):

            # Defaults
            lower = [0]*3
            upper = [i for i in gridvolumes.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            gridvolumes = gridvolumes[lower[0]:upper[0],
                                    lower[1]:upper[1],
                                    lower[2]:upper[2]]
                
        # Ensure gridvolumes is the right shape for subsequent
        # broadcasting with other fields
        gridvolumes = np.expand_dims(gridvolumes,-1)

        return gridvolumes

    def get_subdomlist(self):

        def get_int(name):
            name = name.replace('u','')
            try:
                integer, extension = name.split('.')
                integer = int(integer)
            except ValueError:
                print("Unrecognised fileno:", name.split('.'))
                raise DataNotAvailable
                integer = 10000000000

            return integer

        subdoms = []
        for filename in os.listdir(self.fdir):
            if (filename.find('.h5') != -1):
                subdoms.append(filename)

        subdoms = sorted(subdoms,key=get_int)
        plotfreq = get_int(subdoms[1])-get_int(subdoms[0])
        return subdoms, plotfreq

    def convert(self,filename):
        """
            Convert *.h5 format to ascii *.ff format
        """
        filebase = filename.replace('.h5','')
        if (os.path.isfile(filebase + '.asc')):
            pass
        else: 
            syscall = self.ascii2field + ' -p ' + filebase + '.h5 ' + filebase + '.asc'
            print("Output file in ascii format not founts, " + 
                  "attempting to convert using field2ascii routine")
            try:
                os.system(syscall)
            except:
                raise

        return filebase + '.asc'

    def linear2cosinegrid(self,lingrid):

        """
           Convert a linear grid (from linspace) to a cosine grid
        """
        cosgrid = np.empty(len(lingrid))
        for i in range(0,len(lingrid)):
            cosgrid[i] = -np.cos((lingrid[i]*np.pi)/(self.Ny-1))



    def cosinegrid(self,a,b,Npoints):
        points = np.linspace(0, Npoints, Npoints)
        cosgrid = 0.5*(b+a) - 0.5*(b-a)*np.cos((points*np.pi)/(Npoints))

        return cosgrid


#    def map_data_cosinetolinear(self,cosgrid,Ny=None,a=-1.0,b=1.0):

#        """
#            Map data on a cosine grid to a linear grid 
#        """
#        if Ny == None:
#            Ny = self.ny

#        ycells = np.linspace(0, Ny, Ny)
#        ylin = np.linspace(a, b, Ny)
#        ycos = self.cosinegrid(a,b,Ny-1)
#        lingrid = griddata(ycos, cosgrid, ylin, method='cubic')

        return lingrid

    def read(self,startrec,endrec, binlimits=None, verbose=False, 
                missingrec='raise',wallnormaldir=1):

        return_zeros = False

        nrecs = endrec - startrec + 1
        nbins = [self.nx, self.ny, self.nz]
        lower = np.empty(3); upper = np.empty(3)

        if nrecs > len(self.subdomlist):
            print('Number of records ', nrecs , ' greater than ', len(self.subdomlist) ,
                 ' available:', self.subdomlist)
        elif startrec + nrecs > len(self.subdomlist):
            print('Range of records ', startrec, ' to ', endrec , ' outside ', 
                  startrec, ' to ', len(self.subdomlist)+startrec,
                  ' available:', self.subdomlist)

        def add_laminar(vin,lims):
            v_laminar = self.cosinegrid(a=-1.0, b=1.0, Npoints=self.nry)
            return vin[:] - v_laminar[lims[0]:lims[1]]

        # If bin limits are specified, return only those within range
        for axis in range(3):
            if (binlimits):
                if (binlimits[axis] == None):
                    lower[axis] = 0
                    upper[axis] = int(nbins[axis])
                else:
                    lower[axis] = int(binlimits[axis][0]) 
                    upper[axis] = int(binlimits[axis][1])
            else:
                lower[axis] = 0
                upper[axis] = int(nbins[axis])

        # Efficient memory allocation
        subdata = np.empty((upper[0]-lower[0],
                            upper[1]-lower[1],
                            upper[2]-lower[2],nrecs,self.npercell))

        data =  np.empty((self.nx,
                          self.ny,
                          self.nz,nrecs,self.npercell))

        # Loop through files and insert data
        for plusrec in range(0,nrecs):

            try:
                #fpath = self.fdir + self.subdomlist.pop(startrec+plusrec)
                fpath = self.fdir + self.subdomlist[startrec+plusrec]
            except IndexError:
                if missingrec is 'raise':
                    raise DataNotAvailable
                elif missingrec is 'returnszeros':
                    return_zeros = True
                elif missingrec is 'skip':
                    sys.exit("Skip not developed in Channelflow_rawdata class")

            if return_zeros:
                data = np.zeros((self.nx,
                                 self.ny,
                                 self.nz,self.npercell))
            else:
                data = self.read_field(fpath)

            # insert into array
            subdata[:,:,:,plusrec,:] = data[lower[0]:upper[0],
                                            lower[1]:upper[1],
                                            lower[2]:upper[2], :]


            #Add u component of laminar flow in wallnormal direction
            lims = (lower[wallnormaldir],upper[wallnormaldir])
            subdata[:,:,:,plusrec,0] = np.apply_along_axis(add_laminar,wallnormaldir, 
                                                            subdata[:,:,:,plusrec,0],lims)


            #Reset return zero flag
            return_zeros = False
         
        return subdata

    # Read channelflow field
    def read_asciifield(self,fpath):

        fileasc = self.convert(fpath)
        with open(fileasc,'r') as fobj:
            data = np.fromfile(fobj,sep='\n')
            return np.reshape(data,[self.nx,self.ny,self.nz,self.npercell])

#            for nx in range(self.nx):
#                for ny in range(self.ny):
#                    for nz in range(self.nz):
#                        try:
#                            data[nz,nx,ny,0] = float(f.readline())
#                            data[nz,nx,ny,1] = float(f.readline())
#                            data[nz,nx,ny,2] = float(f.readline())
#                        except:
#                            data[nz,nx,ny,0] = 0.0
#                            data[nz,nx,ny,1] = 0.0
#                            data[nz,nx,ny,2] = 0.0


    # Read channelflow field
    def read_h5field(self,fpath):
        #import h5py
        with h5py.File(fpath,'r') as fobj:
            data = fobj[u'data'].items()[0][1]
            return np.transpose(np.array(data),(1,2,3,0))



