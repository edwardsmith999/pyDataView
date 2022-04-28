#! /usr/bin/env python
import sys
import os

class RawData(object):

    """
        Abstract base class to be inherited by raw data classes

        Authors: Ed Smith and David Trevelyan (October 2014) 

        The RawData class is an abstract base class which defines the interface
        that all rawdata readers must provide. The raw data class is 
        associated with both a data file (e.g. mbins, pVA, etc.) and a
        results directory in which the simulation_header is located. 
        This header contains necessary 
        information that is used to reshape the 1D array of data read 
        from the file into a format that is easy to process later on.

        This class is designed for use in two ways:
            
            1) As a contained object within another that packages
               and returns the data in a 3D field format (from which 
               it may be averaged/summed/sliced into a new format that 
               you may want to plot), i.e. an MDField object, or

            2) For inspection of the numerical values in any binary
               data file in a results folder from the MD code.

    """
    def __init__(self, fdir, fname, dtype, nperbin):

        """
            fdir       -  file directory containing results, string
            fname      -  file path from which to read raw data, string
            dtype      -  datatype string, 'i' for integer, 'd' for float
            nperbin    -  number of items to read per bin, integer
        """

        #Define variables
        if (fdir[-1] != '/'): fdir += '/' 
        self.fdir = fdir
        self.fname = fname
        self.dtype = dtype
        self.nperbin = nperbin
        self.header = self.read_header(fdir)

        #Check if requested output file exists
        if (glob.glob(fdir+fname)):
            self.separate_outfiles = False
        elif (glob.glob(fdir+fname+'.*')):
            self.separate_outfiles = True 
        else:
            print(('Neither ' + fname + ' nor ' + fname + '.* exist.'))
            raise DataNotAvailable

        #Define grid properties
        self.ncells, self.grid, dxyz = self.get_gridtopology()
        self.dx = dxyz[0]; self.dy = dxyz[1]; self.dz = dxyz[2]
        self.maxrec = self.get_maxrec()

        #Check required attributes are defined for RawData class
        self.check_attributes()


    def check_attributes(self):
        """
            Check that the constructor has
            defined the required interface
            and raise error if not
        """

        expected_attr = ["header",
                         "nx", "ny", "nz",
                         "nrx","nry","nrz",
                         "Lx","Ly","Lz",
                         "dx","dy","dz"]
        for attr in expected_attr:
            if(not hasattr(self, attr)):
                print(("RawData class ", self, 
                      " must have attribute ", 
                      attr, " defined in constructor"))
                raise AttributeError


    def read_header(self,fdir):
        """
            Read the simulation parameter from the 
            header data stored in the specified directory
            Note -- all variable should be defined as 
                    variables accessable using
                    self.header.HEADER_DATA_HERE
        """
        sys.exit("read_header not defined")

    def get_maxrec(self):
        """
            Get the maximum record of the avilable data 
            Note -- shouldn't rely on header but actual
                    data present in fdir
        """
        sys.exit("get_maxrec not defined")

    def get_gridtopology(self):
        """
            Get topology of underlying grid 
            Returns:
            
                ncells     - A length-3 list of the number of cells in each
                             direction
                cellspaces - A length-3 list of specifying the locations
                             of the center of each cell of the grid
                cellsizes  - A length-3 list with the width of each cell
        """
        sys.exit("get_gridtopology not defined")

    def get_gridvolumes(self,binlimits=None):
        """
            Get volume of the cells in the grid 
        """
        sys.exit("get_gridvolumes not defined")

    def read(self, startrec, endrec, binlimits=None, verbose=False, 
             missingrec='raise'):
        """
            Read the specified range of data and return as an array in
            the form: 
                data[nx,ny,nz,nrecs,ndata]
            where nx,ny and nz are number of cells in x,y and z respectivly
                  nrecs is the number of recs from startrec to endrec and
                  ndata is the number of datavalue for the current datatype 
                  (e.g. density has 1, velocity has 3, stress has 9, etc)
            Required inputs:

                startrec - seek a specific record with this integer, count
                           from 0.
                endrec   - record at which to finish (integer)

            Return:
                
                data - 4D array of data in one record that was
                       read from the binary data file. The size
                       is (nx, ny, nz, nrecs, ndata) or
                       the equivalent in cylindrical polar.
                
        """
        sys.exit("read not defined")


    def write(self, data, fdir, fname, startrec=0, endrec=None, 
              dryrun=False, verbose=False, separate_outfiles=True):
        """
            Write a 5D array of data in format specified by inhereting objects  
                data[nx,ny,nz,nrecs,ndata]
                where nx,ny and nz are number of cells in x,y and z respectivly
                  nrecs is the number of recs from startrec to endrec and
                  ndata is the number of datavalue for the current datatype 
                  (e.g. density has 1, velocity has 3, stress has 9, etc).          
                  Default format is a binary dump in a single file for all timesteps.

            Optional inputs:

                startrec - starting record to write of data array (integer)
                endrec   - record at which to finish (integer)
                fdir     - default directory to write data (string)
                fname    - filename to use (string)
                separate_outfiles - Write a single file per timestep
            Return:
                
                None      
        """

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
        if (separate_outfiles):

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

        #Write basic header with datasize
        header = fdir + "./simulation_header"
        if (not os.path.exists(header)):
            from datetime import datetime
            date = datetime.today().strftime('%Y%m%d')
            with open(header, "w+") as f:
                f.write("Simulation run on Date;  sim_date ; "  + date+"\n")
                f.write("Averaging Bins in x ;  gnbins(1) ; "  + str(data.shape[0])+"\n")
                f.write("Averaging Bins in y ;  gnbins(2) ; "  + str(data.shape[1])+"\n")
                f.write("Averaging Bins in z ;  gnbins(3) ; "  + str(data.shape[2])+"\n")
                try:
                    f.write("Domain in x ;  globaldomain(1)  ; "  + str(self.domain[0])+"\n")
                    f.write("Domain in y ;  globaldomain(2)  ; "  + str(self.domain[1])+"\n")
                    f.write("Domain in z ;  globaldomain(3)  ; "  + str(self.domain[2])+"\n")
                except AttributeError:
                    f.write("Domain in x ;  globaldomain(1)  ; "  + str(1.)+"\n")
                    f.write("Domain in y ;  globaldomain(2)  ; "  + str(1.)+"\n")
                    f.write("Domain in z ;  globaldomain(3)  ; "  + str(1.)+"\n")

