#! /usr/bin/env python
import numpy as np 
import glob
import os
import sys

from .rawdata import RawData
from .headerdata import MDHeaderData
from .pplexceptions import DataNotAvailable

"""

    MD_RawData Class
    Author: David Trevelyan, April 2013 and Edward Smith
    Updated: Jan 2016 by Edward Smith

    The MD_RawData class is associated with both a data file (e.g.
    mbins, pVA, etc.) and a results directory in which the 
    simulation_header is located. This header contains necessary 
    information that is used to reshape the 1D array of data read 
    from the file into a format that is easy to process later on.
    
    MD_RawData can read any binary data file from the MD code, but
    requires knowledge of the data type (i.e. integer or real) and 
    the number of values per averaging "bin" to read (i.e. velocity
    would require 3 values per bin, one for each cartesian direction).
    
    The header variable cpol_bins is true if the data has been
    averaged in the MD code using cylindrical polar bins: in this 
    case the only difference lies in creating the mesh of the 
    bin topology, because the domain size in cylindrical polar
    coordinates is different to the cartesian domain size that is
    written to the simulation_header.

    This class is designed for use in two ways:
        
        1) As a contained object within another that packages
           and returns the data in a 3D field format (from which 
           it may be averaged/summed/sliced into a new format that 
           you may want to plot), i.e. an MDField object, or

        2) For inspection of the numerical values in any binary
           data file in a results folder from the MD code.

"""

class MD_RawData(RawData):
    
    def __init__(self, fdir, fname, dtype, nperbin):

        """
            fdir       -  file directory containing results, string
            fname      -  file path from which to read raw data, string
            dtype      -  datatype string, 'i' for integer, 'd' for float
            nperbin    -  number of items to read per bin, integer
        """

        if (fdir[-1] != '/'): fdir += '/' 
        self.fdir = fdir
        self.fname = fname

        if (glob.glob(fdir+fname)):
            self.separate_outfiles = False
        elif (glob.glob(fdir+fname+'.*')):
            self.separate_outfiles = True 
        else:
            print(('Neither ' + fname + ' nor ' + fname + '.* exist.'))
            raise DataNotAvailable

        self.header = self.read_header(fdir)
        try:
            self.cpol_bins = bool(int(self.header.cpol_bins))
        except AttributeError:
            self.cpol_bins = False
            self.header.cpol_bins = False
        self.dtype = dtype
        self.nperbin = nperbin
        self.nbins, self.grid, dxyz = self.get_gridtopology()
        self.dx = dxyz[0]; self.dy = dxyz[1]; self.dz = dxyz[2]
        self.maxrec = self.get_maxrec()

    def read_header(self,fdir):
        return MDHeaderData(fdir)

    def get_bintopology(self):
        print("Call to get_bintopology are depreciated, please use get_gridtopology instead")
        return self.get_gridtopology()

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
        
        gnbins  = ([ int(self.header.gnbins1), 
                     int(self.header.gnbins2),
                     int(self.header.gnbins3) ])

        if (self.cpol_bins == True):
            domain = ([ float(self.header.r_io) - float(self.header.r_oi), 
                        2.0*np.pi,
                        float(self.header.globaldomain3) ])
        else:
            domain = ([ float(self.header.globaldomain1),
                        float(self.header.globaldomain2),
                        float(self.header.globaldomain3) ])


        self.domain = domain

        binspaces = []; binsizes = []
        for ixyz in range(3):
            binsize = np.divide(domain[ixyz],gnbins[ixyz])
            binsizes.append(binsize)
            botbincenter = - domain[ixyz]/2. + binsize/2.0
            topbincenter = gnbins[ixyz]*binsize - domain[ixyz]/2. - binsize/2.0 
            binspaces.append(np.linspace(botbincenter,
                                         topbincenter,
                                         num=gnbins[ixyz]))

        return gnbins, binspaces, binsizes


    def get_binvolumes(self,binlimits=None):
        print("Calls to get_binvolumes are deprecated, please use get_gridvolumes instead")
        return self.get_gridvolumes(binlimits=binlimits)

    def get_gridvolumes(self,binlimits=None):

        try:
            binspaces = self.grid
        except AttributeError:
            nbins, binspaces, dxyz = self.get_gridtopology()

        if (self.cpol_bins == True):    

            r_oi = float(self.header.r_oi)
            r, theta, z = np.meshgrid((binspaces[0]+r_oi),
                                       binspaces[1],
                                       binspaces[2],
                                       indexing='ij')


            dr     = binspaces[0][1] - binspaces[0][0]
            dtheta = binspaces[1][1] - binspaces[1][0]
            dz     = binspaces[2][1] - binspaces[2][0]

            r = r + 0.5*dr
            gridvolumes = r*dr*dtheta*dz

        else:

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

    def get_maxrec(self):

        if (glob.glob(self.fdir+self.fname)):

            filesize = os.path.getsize(self.fdir+self.fname)
            if (self.dtype == 'i'):
                maxrec = filesize/(4*self.nperbin*np.prod(self.nbins)) - 1
            elif (self.dtype == 'd'):
                maxrec = filesize/(8*self.nperbin*np.prod(self.nbins)) - 1
            else:
                sys.exit('Unrecognised dtype in MD_RawData.get_maxrec')

        elif (glob.glob(self.fdir+self.fname+'.*')):

            filelist = glob.glob(self.fdir+self.fname+'.*')
            sortedlist = sorted(filelist)
            try:
                maxrec = int(sortedlist[-1].split('.')[-1])
            except ValueError:
                print(("Error in last record, maybe '*', in filename? = ", sortedlist[-1]))
                maxrec = 0
            
        else:
            print(('Neither ' + self.fname + ' nor ' + self.fname + '.* exist.'))
            sys.exit


        return maxrec


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
        recitems = np.product(self.nbins)*self.nperbin
        bindata  = np.empty(int(nrecs*recitems))

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
                                         self.nbins[2],self.nperbin ,nrecs ])
                elif skip_rec:
                    skiprecs.append(plusrec)
                else:
                    try:
                        bindata[istart:iend] = np.fromfile(fobj,dtype=self.dtype)
                    except ValueError:
                        raise
                    fobj.close()

                #Reset ready for next record
                return_zeros = False
                skip_rec = False

       # Else
        else:

            try: 
                fobj = open(self.fdir+self.fname,'rb')
            except:
                if missingrec is 'raise':
                    print(('Unable to find file ' + filepath))    
                    raise DataNotAvailable 
                elif missingrec is 'returnzeros':
                    print(('Unable to find file ' + filepath, '. Returning zeros'))
                    return_zeros = True
                elif missingrec is 'skip':
                    print(('Unable to find file ' + filepath, '. Returning nothing'))
                    skip_rec = True

            # Seek to correct point in the file
            if (self.dtype == 'i'):
                recbytes = 4*recitems
            elif (self.dtype == 'd'):
                recbytes = 8*recitems
            else:
                sys.exit('Unrecognised data type ' + self.dtype + ' specified in read_bins')
 
            seekbyte = startrec*recbytes
            fobj.seek(seekbyte)

            if (verbose):
                print(('Reading {0:s} recs {1:5d} to {2:5d}'.format(
                      self.fname,startrec,endrec)))

            # Get data and reshape with fortran array ordering
            if return_zeros:
                bindata = np.zeros([ self.nbins[0],self.nbins[1],
                                     self.nbins[2],self.nperbin ,nrecs ])
            elif skip_rec:
                return
            else:
                bindata = np.fromfile(fobj, dtype=self.dtype,
                                      count=nrecs*recitems)  

            fobj.close()

        if (verbose):
            print(('Reshaping and transposing {0:s} '.format(self.fname)))

        # Reshape bindata
        bindata = np.reshape( bindata,
                             [ self.nbins[0],
                               self.nbins[1],
                               self.nbins[2],
                               self.nperbin ,
                               nrecs ],
                              order='F')
        bindata = np.transpose(bindata, (0,1,2,4,3))

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


    def write(self, data, fdir, fname, startrec=0, endrec=None, 
              dryrun=False, verbose=False):

        #Use RawData version
        #return RawData.write(self, data, fdir, fname, startrec, endrec, 
        #                     dryrun, verbose, separate_outfiles=self.separate_outfiles)

        #Check this is a 5D array
        assert len(data.shape) == 5

        #Number of records is based on size of data if not specified
        if endrec is None:
            endrec = data.shape[3]

        # Store how many records are to be written
        nrecs = endrec - startrec  
        if nrecs > data.shape[3]:
            raise IOError("Requested startrec and endrec bigger than datasize")

        #print("startrec=",startrec, "endrec=", endrec, "nrecs=", nrecs, "data size=", data.shape)

        # Check whether the records are written separately
        # If so,
        if (self.separate_outfiles):

            # Loop through files and append data
            for plusrec in range(0,nrecs):
                filepath = fdir+fname+'.'+"%07d"%(startrec+plusrec)
                print("Writing", data[:,:,:,plusrec,:].T.shape, " to ", filepath)
                if (not dryrun):
                    with open(filepath,'wb+') as fobj:
                        #We need the transpose to keep in Fortran order
                        fobj.write(data[:,:,:,[plusrec],:].T.tobytes())
        #Otherwise,
        else:
            print("Writing", data[:,:,:,startrec:endrec,:].shape, " to ", fdir+fname)
            if (not dryrun):
                with open(fdir+fname,'wb+') as fobj:
                    fobj.write(data[:,:,:,startrec:endrec,:].T.tobytes())


