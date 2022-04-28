import numpy as np

from .rawdata import RawData
from .pplexceptions import DataNotAvailable

class LAMMPS_RawData(RawData):

    def __init__(self, fdir, fname, readnames):

        if (fdir[-1] != '/'): fdir += '/' 
        self.fdir = fdir
        self.fname = fname
        self.fobj = open(fdir + fname, 'rb')
        self.recoffsets = self.get_recoffsets()
        self.maxrec = len(self.recoffsets) - 1
        self.plotfreq = self.get_plotfreq()
        self.grid = self.get_grid()
        self.nbins = [len(self.grid[i]) for i in range(len(self.grid))]
        self.readindices = self.get_readindices(readnames)
        self.nperbin = len(self.readindices) 
    
    def get_recoffsets(self):
    
        offsets = []
        while True:

            tell = self.fobj.tell()
            line = self.fobj.readline()

            if (len(line.split()) == 3):
                offsets.append(tell) 

            if (line == '' or line == b''):
                break

        return offsets

    def get_plotfreq(self):

        self.fobj.seek(self.recoffsets[0])
        it, ngpoints, nsamples = self.fobj.readline().split()

        return int(it)

    def get_grid(self):

        def uniqueify(seq):
            """ 
                "Remove repeated values, e.g. [1,2,2,3,4,3] => [1,2,3,4]
            """
            seen = set()
            seen_add = seen.add
            return [ x for x in seq if not (x in seen or seen_add(x))]

        self.fobj.seek(self.recoffsets[0])
        it, ngpoints, nsamples = self.fobj.readline().split()
        xlist = []
        ylist = []
        zlist = []
        for point in range(int(ngpoints)):
            lineitems = self.fobj.readline().split()
            xlist.append(float(lineitems[1]))
            ylist.append(float(lineitems[2]))
            zlist.append(float(lineitems[3]))
        
        gridx = np.array(uniqueify(xlist))
        gridy = np.array(uniqueify(ylist))
        gridz = np.array(uniqueify(zlist))

        self.domain = [gridx.max(), gridy.max(), gridz.max()]
        
        return [gridx, gridy, gridz] 

    def get_readindices(self, readnames):
       
        self.fobj.seek(0)
        self.fobj.readline()
        self.fobj.readline()
        line = self.fobj.readline()
        if (b"Chunk Coord1 Coord2 Coord3" in line):
            readindices = []
            linesplit = line.decode("ascii").split()[1:] # Ignore # character at beginning
            for name in readnames:
                readindices.append(linesplit.index(name))
        else:
            print("Couldn't find Chunk coordinate info in "+self.fname)
            raise DataNotAvailable

        return readindices

    def read(self, startrec, endrec, binlimits=None, verbose=False, 
             missingrec='raise'):
        
        # Store how many records are to be read
        nrecs = endrec - startrec + 1 
        # Allocate enough memory in the C library to efficiently insert
        # into bindata
        recitems = np.product(self.nbins)*self.nperbin
        bindata  = np.empty(nrecs*recitems)

        if (verbose):
            print(('Reading {0:s} recs {1:5d} to {2:5d}'.format(
                  self.fname,startrec,endrec)))

        cnt = 0
        for plusrec in range(0, nrecs):

            # Go to the record, read how many lines            
            self.fobj.seek(self.recoffsets[startrec + plusrec]) 
            recdetails = self.fobj.readline().split()
            reclines = int(recdetails[1])

            pos = plusrec*recitems
            # Loop over record's lines
            for plusline in range(reclines):
                lineitems = self.fobj.readline().split()
                for index in self.readindices:
                    bindata[cnt] = float(lineitems[index])
                    cnt += 1

        bindata = np.reshape(bindata,[nrecs,
                                      self.nbins[0],
                                      self.nbins[1],
                                      self.nbins[2],
                                      self.nperbin])
        bindata = np.transpose(bindata, (1,2,3,0,4))

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
