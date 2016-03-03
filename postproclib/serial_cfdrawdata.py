#! /usr/bin/env python
import numpy as np
import os
import glob

from rawdata import RawData
from headerdata import Serial_CFD_HeaderData
from pplexceptions import DataNotAvailable

class Serial_CFD_RawData(RawData):
    
    def __init__(self,fdir,fname,dtype,nperbin):
        if (fdir[-1] != '/'): fdir += '/' 
        self.fdir = fdir
        self.fname = fname
        self.dtype = dtype
        self.nperbin = nperbin
        self.filepath = self.fdir + self.fname + '/'

        if (glob.glob(self.filepath)):
            self.separate_outfiles = False
        elif (glob.glob(self.filepath+'.*')):
            self.separate_outfiles = True 
        else:
            self.separate_outfiles = False

        try:
            self.header = self.read_header(fdir)
            print(self.header)
        except IOError:
            raise DataNotAvailable

        self.grid = self.get_gridtopology()
        self.maxrec = self.get_maxrec()

    def read_header(self,fdir):
        return Serial_CFD_HeaderData(fdir)

    def get_grid(self):
        print("Call to get_grid are depreciated, please use get_gridtopology instead")
        return self.get_gridtopology()

    def get_gridtopology(self):
        #Number of halos
        self.halox = 1
        self.haloy = 1
        self.haloz = 1
        # Number of grid points in main code
        self.nx = int(self.header.nx)+1
        self.ny = int(self.header.ny)+1
        self.nz = int(self.header.nz)+1
        # Number of cell-centered values written with halos
        self.nrx = int(self.nx)-1  #+2*self.halox
        self.nry = int(self.ny)-1+2*self.haloy
        self.nrz = 1 #int(self.nz)-1  #+2*self.haloz
        # Domain lengths
        self.xL = float(self.header.lx)
        self.yL = float(self.header.ly)
        self.zL = float(self.header.lz)
        self.xyzL = [self.xL,self.yL,self.zL]
        # Grid spacing
        self.dx = self.xL/float(self.nrx)
        self.dy = self.yL/float(self.nry-2*self.haloy)
        self.dz = self.zL/float(self.nrz)
        # Linspaces of cell centers, accounting for halos written in y
        gridx = np.linspace(+self.dx/2., self.xL -self.dx/2., num=self.nrx)
        # NOTE SHIFTED BY HALF A CELL SO IT MATCHES THE OVERLAPPED MD CASE
        gridy = np.linspace(-self.dy/2., self.yL +self.dy/2., num=self.nry)-self.dy
        print(self.yL,self.ny,self.dy,gridy)
        gridz = np.linspace(+self.dz/2., self.zL -self.dz/2., num=self.nrz)
        grid = [gridx,gridy,gridz]
        return grid 

    def get_maxrec(self):

        if (glob.glob(self.fdir+self.fname)):

            filesize = os.path.getsize(self.fdir+self.fname)
            if (self.dtype == 'i'):
                maxrec = filesize/(4*self.nperbin*self.nrx*self.nry*self.nrz) - 1
            elif (self.dtype == 'd'):
                maxrec = filesize/(8*self.nperbin*self.nrx*self.nry*self.nrz) - 1
            else:
                quit('Unrecognised dtype in MD_RawData.get_maxrec')

        elif (glob.glob(self.fdir+self.fname+'.*')):

            filelist = glob.glob(self.fdir+self.fname+'.*')
            sortedlist = sorted(filelist)
            maxrec = int(sortedlist[-1].split('.')[-1])
            
        else:
            print('Neither ' + self.fname + ' nor ' + self.fname + '.* exist.')
            raise DataNotAvailable

        return maxrec

    def read(self, startrec, endrec, binlimits=None, verbose=False, missingrec='raise'):

        """
            Required inputs:

                startrec - seek a specific record with this integer, count
                           from 0.
                endrec   - record at which to finish (integer)

            Return:
                
                bindata - 4D array of data in one record that was
                          read from the binary data file. The size
                          is (nbinsx, nbinsy, nbinsz, nperbin) or
                          the equivalent in cylindrical polar.
                
        """

        #return_zeros if data cannot be obtained
        return_zeros = False
      
        # Store how many records are to be read
        nrecs = endrec - startrec + 1 
        # Allocate enough memory in the C library to efficiently insert
        # into bindata
        recitems = self.nrx*self.nry*self.nrz*self.nperbin
        bindata  = np.empty(nrecs*recitems)

        # Check whether the records are written separately
        # If so
        if (self.separate_outfiles):

            # Loop through files and append data
            for plusrec in range(0,nrecs):

                filepath = self.fdir+self.fname+'.'+"%07d"%(startrec+plusrec)
                try: 
                    fobj = open(filepath,'rb')
                except:
                    if missingrec is 'raise':
                        quit('Unable to find file ' + filepath)    
                    else:
                        print('Unable to find file ' + filepath)
                        return_zeros = True

                istart = plusrec*recitems
                iend = istart + recitems
                if (verbose):
                    print('Reading {0:s} rec {1:5d}'.format(
                          self.fname,startrec+plusrec))
                if return_zeros:
                    bindata = np.zeros([ self.nrx,self.nry,self.nrz,
                                         self.nperbin ,nrecs ])
                else:
                    bindata[istart:iend] = np.fromfile(fobj,dtype=self.dtype)
                    fobj.close()

       # Else
        else:

            try: 
                fobj = open(self.fdir+self.fname,'rb')
            except:
                if missingrec is 'raise':
                    print('Unable to find file ' + self.fname)
                    raise DataNotAvailable
                elif missingrec is 'returnzeros':
                    print('Unable to find file ' + self.fname)
                    return_zeros = True

            # Seek to correct point in the file
            if (self.dtype == 'i'):
                recbytes = 4*recitems
            elif (self.dtype == 'd'):
                recbytes = 8*recitems
            else:
                if missingrec is 'raise':
                    print('Unable to find file ' + self.fname)
                    raise DataNotAvailable
                elif missingrec is 'returnzeros':
                    print('Unable to find file ' + self.fname)
                    return_zeros = True

            seekbyte = startrec*recbytes
            fobj.seek(seekbyte)

            if (verbose):
                print('Reading {0:s} recs {1:5d} to {2:5d}'.format(
                      self.fname,startrec,endrec))

            # Get data and reshape with fortran array ordering
            if return_zeros:
                bindata = np.zeros([ self.nrx,self.nry,self.nrz,
                                     self.nperbin ,nrecs ])
            else:
                bindata = np.fromfile(fobj, dtype=self.dtype,
                                      count=nrecs*recitems)  

            fobj.close()

        if (verbose):
            print('Reshaping and transposing {0:s} '.format(self.fname))

        # Reshape bindata
        bindata = np.reshape( bindata,
                             [ self.nrx,
                               self.nry,
                               self.nrz,
                               self.nperbin ,
                               nrecs ],
                              order='F')
        bindata = np.transpose(bindata, (0,1,2,4,3))

        # If bin limits are specified, return only those within range
        if (binlimits):

            if (verbose):
                print('bindata.shape = {0:s}'.format(str(bindata.shape)))
                print('Extracting bins {0:s} from {1:s} '.format(
                      str(binlimits),self.fname))
            # Defaults
            lower = [0]*3
            upper = [i for i in bindata.shape] 
    
            for axis in range(3):
                if (binlimits[axis] == None):
                    continue
                else:
                    lower[axis] = binlimits[axis][0] 
                    upper[axis] = binlimits[axis][1] 

            bindata = bindata[lower[0]:upper[0],
                              lower[1]:upper[1],
                              lower[2]:upper[2], :, :]


            if (verbose):
                print('new bindata.shape = {0:s}'.format(str(bindata.shape)))

        return bindata
        
