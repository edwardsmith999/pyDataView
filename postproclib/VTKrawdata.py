import numpy as np
import pyvista as pv
import glob

from .rawdata import RawData
from .pplexceptions import DataNotAvailable

class VTK_RawData(RawData):
    """
        A reader for vtk objects assuming
        a RectilinearGrid, example tested is as
        written by LAMMPS grid system 
    """

    def __init__(self, fdir, fname):

        if (fdir[-1] != '/'): fdir += '/' 
        self.fdir = fdir
        self.fname = fname
        self.filelist = glob.glob(self.fdir+self.fname+'.*.vtr')
        self.filelist = sorted(self.filelist)
        self.plotfreq = self.get_plotfreq()
        self.nperbin = self.get_nperbin()
        if self.nperbin == 1:
            self.key = 'Scalar'
        elif self.nperbin == 3:
            self.key = 'Vector'
        else:
            raise IOError("nperbin should be 1 (Scalar) or 3 (Vector) or VTK format")
            
        #Maximum record is integer number of records, not timestep
        #maximum record written at
        #int(self.get_maxrecNo()/float(self.plotfreq))+1
        self.maxrec = len(self.filelist)-1
        self.nbins, self.grid, dxyz = self.get_gridtopology()
        self.dx = dxyz[0]; self.dy = dxyz[1]; self.dz = dxyz[2]

    def get_maxrecNo(self):

        try:
            maxrec = int(self.filelist[-1].split('.')[-2])
        except ValueError:
            print(("Error in last record, maybe '*', in filename? = ", self.filelist[-1]))
            maxrec = 0
        
        return maxrec
    

    def get_plotfreq(self):

        if (len(self.filelist) > 1):
            firstno = int(self.filelist[0].split(".")[-2])
            secondno = int(self.filelist[1].split(".")[-2])
            return  secondno-firstno
        else:
            return None

    def get_nperbin(self):
        fdata = pv.read(self.filelist[0])
        if fdata.cell_data.keys()[0] == "Scalar":
            return 1
        elif fdata.cell_data.keys()[0] == "Vector":
            return 3
        else:
            raise IOError("VTK format is not Scalar or Vector")
        

    def get_gridtopology(self):


        """
            Returns:
            
                gnbins    - A length-3 list of the number of bins in each
                            direction, and
                binspaces - A length-3 list of numpy linspaces specifying
                            the locations of the center of each bin in a
                            uniform grid (one linspace for each direction)
                binsizes  - A length-3 list with the size of each bin

        """
        
        #Read any file as grid should be the same
        fdata = pv.read(self.filelist[0])
        #gnbins  = (fdata.extent[1], fdata.extent[3], fdata.extent[5])
        gnbins  = (fdata.x.shape[0]-1, fdata.y.shape[0]-1, fdata.z.shape[0]-1)

        self.domain = [fdata.x[-1], fdata.y[-1], fdata.z[-1]]

        binspaces = [0.5*(fdata.x[:-1] + fdata.x[1:]), 
                     0.5*(fdata.y[:-1] + fdata.y[1:]),
                     0.5*(fdata.z[:-1] + fdata.z[1:])]

        binsizes = []
        for ixyz in range(3):
            try:
                binsizes.append(binspaces[ixyz][1]-binspaces[ixyz][0])
            except IndexError:
                binsizes.append(self.domain[ixyz])
            
        return gnbins, binspaces, binsizes

    def read(self, startrec, endrec, binlimits=None, verbose=False, 
             missingrec='raise'):

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

        #return_zeros or skip_rec if data cannot be obtained?
        return_zeros = False; skip_rec = False; skiprecs = []

        # Store how many records are to be read
        startrec = int(startrec)
        endrec = int(endrec)
        nrecs = endrec - startrec + 1 
        # Allocate enough memory in the C library to efficiently insert
        # into bindata
        recitems = np.product(self.nbins)
        bindata  = np.empty([int(nrecs*recitems), self.nperbin])

        # Check whether the records are written separately
        # If so

        # Loop through files and append data
        for plusrec in range(0,nrecs):
            filepath = (self.fdir + self.fname + '.' 
                        + "%08d"%((startrec+plusrec)*self.plotfreq)+".vtr")
            try: 
                #Use PyVTK plotting library
                fobj = pv.read(filepath)
            except:
                if missingrec is 'raise':
                    print(('Unable to find file ' + filepath))    
                    raise DataNotAvailable
                elif missingrec is 'returnzeros':
                    print(('Unable to find file ' + filepath, '. Returning zeros'))
                    return_zeros = True
                elif missingrec is 'skip':
                    print(('Unable to find file ' + filepath, '. Reducing returned records by one'))
                    skip_rec = True

            istart = plusrec*recitems
            iend = istart + recitems
            if (verbose):
                print(('Reading {0:s} rec {1:5d}'.format(
                      self.fname,startrec+plusrec)))
            if return_zeros:
                bindata = np.zeros([ self.nbins[0],self.nbins[1],
                                     self.nbins[2],self.nperbin, nrecs])
            elif skip_rec:
                skiprecs.append(plusrec)
            else:
                try:
                    if self.key == "Scalar":
                        bindata[istart:iend,0] = fobj.cell_data.get_array(self.key)
                    elif self.key == "Vector":
                        bindata[istart:iend,:] = fobj.cell_data.get_array(self.key)

                except ValueError:
                    raise

            #Reset ready for next record
            return_zeros = False
            skip_rec = False

        if (verbose):
            print(('Reshaping and transposing {0:s} '.format(self.fname)))

        # Reshape bindata
        bindata = np.reshape( bindata,
                             [ self.nbins[0],
                               self.nbins[1],
                               self.nbins[2],
                               nrecs, 
                               self.nperbin
                              ],
                              order='F')

        #If records were missing and skip record requested
        if skiprecs != []:
            bindata = np.delete(bindata,skiprecs,axis=3)

        # If bin limits are specified, return only those within range
        if (binlimits):

            if (verbose):
                print(('bindata.shape = {0:s}'.format(str(bindata.shape))))
                print(('Extracting bins {0:s} from {1:s} '.format(
                      str(binlimits),self.fname)))
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
                print(('new bindata.shape = {0:s}'.format(str(bindata.shape))))

        return bindata

    def get_gridvolumes(self,binlimits=None):

        try:
            binspaces = self.grid
        except AttributeError:
            nbins, binspaces, dxyz = self.get_gridtopology()

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

